import os
import yaml

from dotenv import load_dotenv

from fastapi import APIRouter, Query

router = APIRouter()

load_dotenv()

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

    return str(v).lower() in (
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


@router.get("/effective-config")
def effective_config(
    set: list[str] = Query(default=[]),
):

    config = DEFAULTS.copy()

    try:
        with open("config.development.yaml") as f:
            config.update(
                yaml.safe_load(f) or {}
            )
    except FileNotFoundError:
        pass

    if os.getenv("NUM_WORKERS"):
        config["workers"] = int(
            os.getenv("NUM_WORKERS")
        )

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env, key in mapping.items():

        value = os.getenv(env)

        if value is not None:
            config[key] = coerce(
                key,
                value,
            )

    for item in set:

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        config[key] = coerce(
            key,
            value,
        )

    config["api_key"] = "****"

    return config
