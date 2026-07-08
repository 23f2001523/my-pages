from fastapi import FastAPI

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

# Register all routers
app.include_router(stats.router)
app.include_router(verify.router)
app.include_router(config_api.router)
app.include_router(analytics.router)
app.include_router(observability.router)
app.include_router(orders.router)
app.include_router(middleware_api.router)
app.include_router(extract.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "TDS Exam API"
    }
