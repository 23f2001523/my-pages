import base64
import math
import time
import uuid
from collections import defaultdict, deque
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

TOTAL_ORDERS = 58
RATE_LIMIT = 16
WINDOW = 10

app = FastAPI()

# Browser-based grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fixed catalog
CATALOG = [
    {
        "id": i,
        "item": f"Order {i}",
    }
    for i in range(1, TOTAL_ORDERS + 1)
]

# Idempotency storage
IDEMPOTENCY = {}

# Rate limit buckets
BUCKETS = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):

    # Never rate-limit CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    client = request.headers.get("X-Client-Id")

    # Only rate-limit requests that actually provide a client ID.
    if client:

        now = time.time()

        bucket = BUCKETS[client]

        while bucket and now - bucket[0] >= WINDOW:
            bucket.popleft()

        if len(bucket) >= RATE_LIMIT:

            retry = max(
                1,
                math.ceil(
                    WINDOW - (now - bucket[0])
                ),
            )

            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(retry)
                },
                content={
                    "detail": "Rate limit exceeded"
                },
            )

        bucket.append(now)

    return await call_next(request)


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/orders")
def create_order(
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
    )
):

    if idempotency_key in IDEMPOTENCY:

        return JSONResponse(
            status_code=200,
            content=IDEMPOTENCY[idempotency_key],
        )

    order = {
        "id": str(uuid.uuid4())
    }

    IDEMPOTENCY[idempotency_key] = order

    return JSONResponse(
        status_code=201,
        content=order,
    )


@app.get("/orders")
def list_orders(
    limit: int = 10,
    cursor: Optional[str] = None,
):

    start = 0

    if cursor:

        try:
            start = int(
                base64.b64decode(
                    cursor.encode()
                ).decode()
            )
        except Exception:
            start = 0

    start = max(
        0,
        min(
            start,
            TOTAL_ORDERS,
        ),
    )

    end = min(
        start + limit,
        TOTAL_ORDERS,
    )

    items = CATALOG[start:end]

    next_cursor = None

    if end < TOTAL_ORDERS:

        next_cursor = base64.b64encode(
            str(end).encode()
        ).decode()

    return {
        "items": items,
        "next_cursor": next_cursor,
    }