from fastapi import FastAPI, Request
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
import uuid
from collections import deque

app = FastAPI()

START_TIME = time.time()

# Prometheus counter
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# store last 1000 logs
LOGS = deque(maxlen=1000)


@app.middleware("http")
async def metrics_and_logs(request: Request, call_next):

    REQUEST_COUNTER.inc()

    request_id = str(uuid.uuid4())

    LOGS.append({
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    })

    response = await call_next(request)
    return response


@app.get("/work")
def work(n: int):

    # simulate work
    for _ in range(n):
        pass

    return {
        "email": "23f2001523@ds.study.iitm.ac.in",
        "done": n
    }


@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/healthz")
def health():
    return {
        "status": "ok",
        "uptime_s": time.time() - START_TIME
    }


@app.get("/logs/tail")
def logs(limit: int = 10):
    return list(LOGS)[-limit:]
