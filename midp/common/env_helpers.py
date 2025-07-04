import json
import os
from typing import Any, Optional

from midp.log_factory import midp_logger

log = midp_logger('env')


def required_env(env: str, help: Optional[str] = None) -> str:
    set_value = os.getenv(env)

    if set_value is None or set_value == '':
        raise RuntimeError(f'REQUIRED ENV "{env}": {help or "Your need to set this environment variable."}')
    else:
        log.debug(f'ENV "{env}" = {json.dumps(set_value)})')

    return set_value


def optional_env(env: str, default: Any = None, help: Optional[str] = None) -> str:
    set_value = os.getenv(env)

    if set_value is None:
        log.debug(f'ENV "{env}": {help}')
        log.debug(f'ENV "{env}": It is not defined. The default value ({json.dumps(default)}) is used.')

        return default
    else:
        log.debug(f'ENV "{env}" = {json.dumps(set_value)})')

    return set_value
