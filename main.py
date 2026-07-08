import base64
import time
import uuid
from collections import defaultdict, deque
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

TOTAL_ORDERS = 58
RATE_LIMIT = 16
WINDOW = 10

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fixed catalog
ORDERS = [
    {
        "id": i,
        "item": f"Order {i}"
    }
    for i in range(1, TOTAL_ORDERS + 1)
]

# Idempotency storage
idempotency_store = {}

# Rate limiting storage
client_buckets = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    client = request.headers.get("X-Client-Id")

    # No client ID -> don't rate limit
    if client is None:
        return await call_next(request)

    now = time.time()
    bucket = client_buckets[client]

    while bucket and now - bucket[0] >= WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        retry_after = max(1, int(WINDOW - (now - bucket[0])))
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            content={"detail": "Rate limit exceeded"},
        )

    bucket.append(now)

    return await call_next(request)


@app.post("/orders", status_code=201)
def create_order(
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    if idempotency_key in idempotency_store:
        return idempotency_store[idempotency_key]

    order = {
        "id": str(uuid.uuid4())
    }

    idempotency_store[idempotency_key] = order
    return order


@app.get("/orders")
def list_orders(limit: int = 10, cursor: Optional[str] = None):
    start = 0

    if cursor:
        try:
            start = int(base64.b64decode(cursor.encode()).decode())
        except Exception:
            start = 0

    start = max(0, min(start, TOTAL_ORDERS))
    end = min(start + limit, TOTAL_ORDERS)

    items = ORDERS[start:end]

    next_cursor = None
    if end < TOTAL_ORDERS:
        next_cursor = base64.b64encode(str(end).encode()).decode()

    return {
        "items": items,
        "next_cursor": next_cursor
    }
