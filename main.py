import os
import yaml
from dotenv import load_dotenv

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # YAML layer
    try:
        with open("config.development.yaml") as f:
            config.update(yaml.safe_load(f) or {})
    except FileNotFoundError:
        pass

    # .env layer
    if os.getenv("NUM_WORKERS") is not None:
        config["workers"] = int(os.getenv("NUM_WORKERS"))

    # OS environment layer
    env_map = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_name, key in env_map.items():
        val = os.getenv(env_name)
        if val is not None:
            config[key] = coerce(key, val)

    # CLI overrides (?set=key=value)
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        config[key] = coerce(key, value)

    # Mask secret
    config["api_key"] = "****"

    return config
