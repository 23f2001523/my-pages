import math
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "23f2001523@ds.study.iitm.ac.in"

RATE_LIMIT = 10
WINDOW = 10

ALLOWED_ORIGINS = [
    "https://app-yc1yo9.example.com",
    "https://exam.sanand.workers.dev",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

BUCKETS = defaultdict(deque)


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ---------- Skip OPTIONS ----------
    if request.method != "OPTIONS":

        client = request.headers.get("X-Client-Id")

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

                response = JSONResponse(
                    status_code=429,
                    headers={
                        "Retry-After": str(retry),
                    },
                    content={
                        "detail": "Rate limit exceeded",
                    },
                )

                response.headers["X-Request-ID"] = request_id

                return response

            bucket.append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def root():
    return {
        "status": "ok"
    }


@app.get("/ping")
def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }