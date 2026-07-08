import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "23f2001523@ds.study.iitm.ac.in"
ASSIGNED_ORIGIN = "https://exam.sanand.workers.dev/"

RATE_LIMIT = 10
WINDOW = 10

app = FastAPI()

# Add your assigned origin. If you know the exam origin, add it here too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-yc1yo9.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

client_buckets = defaultdict(deque)


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ---------- Skip rate limit for preflight ----------
    if request.method != "OPTIONS":
        client = request.headers.get("X-Client-Id")

        if client:
            now = time.time()
            bucket = client_buckets[client]

            while bucket and now - bucket[0] >= WINDOW:
                bucket.popleft()

            if len(bucket) >= RATE_LIMIT:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )
                response.headers["X-Request-ID"] = request_id
                return response

            bucket.append(now)

    response = await call_next(request)

    # Always echo request ID in response header
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.options("/ping")
def ping_options():
    # CORSMiddleware will add the CORS headers
    return {}
