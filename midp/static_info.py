import os
from typing import Optional

from pydantic import BaseModel


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
ACCESS_TOKEN_TTL = 3600
REFRESH_TOKEN_TTL = 3600 * 24 * 7
PUBLIC_FILE_PATH = os.path.join(os.path.dirname(__file__), 'public')
WEB_FRONTEND_FILE_PATH = os.path.join(os.path.dirname(__file__), 'webui')
DEFAULT_APP_NAME = 'dev.shiroyuki.com'
