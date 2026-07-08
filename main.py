from fastapi import FastAPI
from redis import Redis

app = FastAPI()

# "redis" is the Docker Compose service name
r = Redis(host="redis", port=6379, decode_responses=True)


@app.post("/hit/{key}")
def hit(key: str):
    count = r.incr(key)
    return {
        "key": key,
        "count": count
    }


@app.get("/count/{key}")
def count(key: str):
    value = r.get(key)
    return {
        "key": key,
        "count": int(value) if value else 0
    }


@app.get("/healthz")
def health():
    try:
        r.ping()
        return {
            "status": "ok",
            "redis": "up"
        }
    except Exception:
        return {
            "status": "error",
            "redis": "down"
        }
