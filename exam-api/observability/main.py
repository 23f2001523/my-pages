import time
import uuid
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import (
    Counter,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

EMAIL = "23f2001523@ds.study.iitm.ac.in"

app = FastAPI()

START = time.time()

REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP Requests",
)

LOGS = deque(maxlen=1000)


@app.middleware("http")
async def logging(request: Request, call_next):

    REQUEST_COUNTER.inc()

    rid = str(uuid.uuid4())

    LOGS.append(
        {
            "level": "INFO",
            "ts": time.time(),
            "path": request.url.path,
            "request_id": rid,
        }
    )

    response = await call_next(request)

    return response


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/work")
def work(n: int):

    for _ in range(n):
        pass

    return {
        "email": EMAIL,
        "done": n,
    }


@app.get("/metrics")
def metrics():

    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/healthz")
def health():

    return {
        "status": "ok",
        "uptime_s": time.time() - START,
    }


@app.get("/logs/tail")
def tail(limit: int = 10):

    return list(LOGS)[-limit:]