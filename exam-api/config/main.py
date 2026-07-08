import os

import yaml
from dotenv import load_dotenv

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Required so the browser-based grader can call the endpoint.
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


def to_bool(value):
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def coerce(key, value):

    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/effective-config")
def effective_config(
    set: list[str] = Query(default=[]),
):

    config = DEFAULTS.copy()

    # ----------------------------------
    # YAML
    # ----------------------------------

    try:
        with open("config.development.yaml") as f:
            config.update(
                yaml.safe_load(f) or {}
            )
    except FileNotFoundError:
        pass

    # ----------------------------------
    # .env
    # ----------------------------------

    workers = os.getenv("NUM_WORKERS")

    if workers is not None:
        config["workers"] = int(workers)

    # ----------------------------------
    # OS Environment
    # ----------------------------------

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in mapping.items():

        value = os.getenv(env_key)

        if value is not None:
            config[cfg_key] = coerce(
                cfg_key,
                value,
            )

    # ----------------------------------
    # CLI overrides
    # ----------------------------------

    for item in set:

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        config[key] = coerce(
            key,
            value,
        )

    # Never expose secrets.
    config["api_key"] = "****"

    return config