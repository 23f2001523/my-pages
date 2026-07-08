import time
import uuid
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

ALLOWED_ORIGIN = "https://dash-1cxm3t.example.com"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Process-Time"] = f"{elapsed:.6f}"

        return response

app.add_middleware(MetricsMiddleware)


@app.get("/stats")
async def stats(values: str = Query(...)):
    nums = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": "23f2001523@ds.study.iitm.ac.in",
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }