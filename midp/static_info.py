import os
import re
from typing import Optional

from pydantic import BaseModel

from midp.common.env_helpers import optional_env
from midp.log_factory import midp_logger

log = midp_logger('mini-idp')


class __VersionInfo(BaseModel):
    major: int = 0
    minor: int = 1
    patch: int = 0
    label: Optional[str] = None

    def __str__(self):
        signature: str = f'{self.major}.{self.minor}'

        if self.patch > 0:
            signature += '.' + str(self.patch)

        if self.label and self.label.strip():
            signature += '-' + self.label.strip()

        return signature


ARTIFACT_ID = 'mini-idp'
VERSION_INFO = __VersionInfo()
VERSION = str(VERSION_INFO)  # deferred to version_info
VERIFICATION_TTL = 600

ACCESS_TOKEN_TTL_DEFAULT = 60 * 30  # 30 minutes
ACCESS_TOKEN_TTL_SAFE_MAX = ACCESS_TOKEN_TTL_DEFAULT * 48  # 1 day
ACCESS_TOKEN_TTL = ACCESS_TOKEN_TTL_DEFAULT

OVERRIDING_ACCESS_TOKEN_TTL_RAW = optional_env('MINI_IDP_ACCESS_TOKEN_TTL',
                                           default='',
                                           help='The TTL for the access token in second')

if OVERRIDING_ACCESS_TOKEN_TTL_RAW:
    if re.search(r'^\d+$', OVERRIDING_ACCESS_TOKEN_TTL_RAW):
        OVERRIDING_ACCESS_TOKEN_TTL = int(OVERRIDING_ACCESS_TOKEN_TTL_RAW)
        if OVERRIDING_ACCESS_TOKEN_TTL < 0:
            raise RuntimeError('The TTL for access tokens must be positive number.')
        elif OVERRIDING_ACCESS_TOKEN_TTL > ACCESS_TOKEN_TTL_SAFE_MAX:
            log.warning(f"The TTL for access tokens is longer the suggested one "
                        f"({ACCESS_TOKEN_TTL_SAFE_MAX}s).")
        # Override the TTL for access tokens.
        ACCESS_TOKEN_TTL = OVERRIDING_ACCESS_TOKEN_TTL
        log.warning(f"The TTL for access tokens is set to {ACCESS_TOKEN_TTL}s.")
    else:
        raise RuntimeError('The given/overriding TTL for access tokens must be positive number.')
else:
    log.warning("The \"default\" TTL for access tokens is used.")

REFRESH_TOKEN_TTL_DEFAULT = ACCESS_TOKEN_TTL_DEFAULT * 24  # 12 hours
REFRESH_TOKEN_TTL_SAFE_MAX = ACCESS_TOKEN_TTL_SAFE_MAX * 7  # 1 Week
REFRESH_TOKEN_TTL = REFRESH_TOKEN_TTL_DEFAULT

OVERRIDING_REFRESH_TOKEN_TTL_RAW = optional_env('MINI_IDP_REFRESH_TOKEN_TTL',
                                            default='',
                                            help='The TTL for the refresh token in second')

if OVERRIDING_REFRESH_TOKEN_TTL_RAW:
    if re.search(r'^\d+$', OVERRIDING_REFRESH_TOKEN_TTL_RAW):
        OVERRIDING_REFRESH_TOKEN_TTL = int(OVERRIDING_REFRESH_TOKEN_TTL_RAW)
        if OVERRIDING_REFRESH_TOKEN_TTL < 0:
            raise RuntimeError('The TTL for refresh tokens must be positive number.')
        elif OVERRIDING_REFRESH_TOKEN_TTL > REFRESH_TOKEN_TTL_SAFE_MAX:
            log.warning(f"The TTL for refresh tokens is longer the suggested one "
                        f"({REFRESH_TOKEN_TTL_SAFE_MAX}s).")
        # Override the TTL for refresh tokens.
        REFRESH_TOKEN_TTL = OVERRIDING_REFRESH_TOKEN_TTL
        log.warning(f"The TTL for refresh tokens is set to {REFRESH_TOKEN_TTL}s.")
    else:
        raise RuntimeError('The given/overriding TTL for refresh tokens must be positive number.')
else:
    log.warning("The \"default\" TTL for refresh tokens is used.")

PUBLIC_FILE_PATH = os.path.join(os.path.dirname(__file__), 'public')
WEB_FRONTEND_FILE_PATH = os.path.join(os.path.dirname(__file__), 'webui')
DEFAULT_APP_NAME = 'idp.dev.shiroyuki.com'
BOOTING_OPTIONS = optional_env('MINI_IDP_BOOTING_OPTIONS',
                               '',
                               help="Mini IDP booting options").split(',')
SELF_REFERENCE_URI = optional_env('MINI_IDP_SELF_REF_URI',
                                  'http://localhost:8081/',
                                  help="Self reference URI back to this service")
IN_DEBUG_MODE = optional_env('MINI_IDP_DEBUG', '', help="The debug mode flag").lower() in ['1', 'true']
