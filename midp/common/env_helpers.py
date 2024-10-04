import os
from typing import Any


def optional_env(env: str, default: Any = None) -> str:
    return os.getenv(env) or default
