import time
import uuid
import base64
from collections import defaultdict, deque

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# -----------------------------
# CONFIG
# -----------------------------
TOTAL_ORDERS = 58
RATE_LIMIT = 16          # requests
WINDOW = 10              # seconds

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Fixed catalog
# -----------------------------
ORDERS = [
    {
        "id": i,
        "item": f"Order {i}"
    }
    for i in range(1, TOTAL_ORDERS + 1)
]

# -----------------------------
# Idempotency storage
# -----------------------------
idempotency = {}

# -----------------------------
# Rate limiter
# -----------------------------
client_requests = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request, call_next):

    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    q = client_requests[client]

    while q and now - q[0] >= WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:

        retry = WINDOW - (now - q[0])

        return Response(
            status_code=429,
            headers={
                "Retry-After": str(max(1, int(retry)))
            }
        )

    q.append(now)

    return await call_next(request)


# ---------------------------------------------------
# POST /orders
# ---------------------------------------------------
@app.post("/orders", status_code=201)
def create_order(idempotency_key: str = Header(..., alias="Idempotency-Key")):

    if idempotency_key in idempotency:
        return idempotency[idempotency_key]

    order = {
        "id": str(uuid.uuid4())
    }

    idempotency[idempotency_key] = order

    return order


# ---------------------------------------------------
# GET /orders
# ---------------------------------------------------
@app.get("/orders")
def list_orders(limit: int = 10, cursor: str | None = None):

    start = 0

    if cursor:
        try:
            start = int(base64.b64decode(cursor).decode())
        except Exception:
            start = 0

    end = min(start + limit, TOTAL_ORDERS)

    items = ORDERS[start:end]

    next_cursor = None

    if end < TOTAL_ORDERS:
        next_cursor = base64.b64encode(
            str(end).encode()
        ).decode()

    return {
        "items": items,
        "next_cursor": next_cursor
    }
