from fastapi import FastAPI, Request
from fastapi.responses import Response

from routers import (
    analytics,
    config_api,
    extract,
    middleware_api,
    observability,
    orders,
    stats,
    verify,
)

app = FastAPI(
    title="TDS Exam API",
    version="1.0"
)

app.include_router(stats.router)
app.include_router(verify.router)
app.include_router(config_api.router)
app.include_router(analytics.router)
app.include_router(observability.router)
app.include_router(orders.router)
app.include_router(middleware_api.router)
app.include_router(extract.router)


@app.middleware("http")
async def cors_dispatch(request: Request, call_next):

    response = await call_next(request)

    origin = request.headers.get("Origin")

    if not origin:
        return response

    allowed = None

    if request.url.path.startswith("/stats"):
        if origin == "https://dash-1cxm3t.example.com":
            allowed = origin

    elif request.url.path.startswith("/ping"):
        if origin in (
            "https://app-yc1yo9.example.com",
            "https://exam.sanand.workers.dev",
        ):
            allowed = origin

    elif request.url.path.startswith("/analytics"):
        allowed = "*"

    elif request.url.path.startswith("/orders"):
        allowed = "*"

    elif request.url.path.startswith("/effective-config"):
        allowed = "*"

    if allowed:

        response.headers["Access-Control-Allow-Origin"] = allowed
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"

    return response


@app.options("/{path:path}")
async def options(path: str):

    return Response(status_code=200)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "TDS Exam API"
    }
