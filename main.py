import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

EMAIL = "23f2001523@ds.study.iitm.ac.in"

ASSIGNED_ORIGIN = "https://app-yc1yo9.example.com"

RATE_LIMIT = 10
WINDOW = 10

client_buckets = defaultdict(deque)


# -------------------------------------------------------
# Request Context Middleware
# -------------------------------------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -------------------------------------------------------
# CORS Middleware
# -------------------------------------------------------
@app.middleware("http")
async def cors(request: Request, call_next):

    origin = request.headers.get("Origin")

    if request.method == "OPTIONS":

        response = JSONResponse({})

    else:

        response = await call_next(request)

    if origin:

        # Allow assigned origin
        if origin == ASSIGNED_ORIGIN:

            response.headers["Access-Control-Allow-Origin"] = origin

        # Allow the exam page as well
        elif "exam" in origin.lower():

            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"

    return response


# -------------------------------------------------------
# Rate Limiter
# -------------------------------------------------------
@app.middleware("http")
async def rate_limit(request: Request, call_next):

    if request.method == "OPTIONS":
        return await call_next(request)

    client = request.headers.get("X-Client-Id")

    if client:

        now = time.time()

        bucket = client_buckets[client]

        while bucket and now - bucket[0] >= WINDOW:
            bucket.popleft()

        if len(bucket) >= RATE_LIMIT:

            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        bucket.append(now)

    return await call_next(request)


# -------------------------------------------------------
# Endpoint
# -------------------------------------------------------
@app.get("/ping")
def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
