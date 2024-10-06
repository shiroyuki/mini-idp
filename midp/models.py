from typing import Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field

from midp.iam.models import IAMScope, IAMRole, IAMUser, IAMOAuthClient, IAMPolicy


class Realm(BaseModel):
    __tbl__ = 'realm'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    scopes: List[IAMScope] = Field(default_factory=list)  # Auxiliary Property: Augmented
    roles: List[IAMRole] = Field(default_factory=list)  # Auxiliary Property: Augmented
    users: List[IAMUser] = Field(default_factory=list)  # Auxiliary Property: Augmented
    clients: List[IAMOAuthClient] = Field(default_factory=list)  # Auxiliary Property: Augmented
    policies: List[IAMPolicy] = Field(default_factory=list)  # Auxiliary Property: Augmented


class GrantType:
    # The authorization flow
    AUTHORIZATION = 'authorization'

    # The client-credentials flow
    CLIENT_CREDENTIALS = 'client_credentials'

    # The device-code flow
    DEVICE_CODE = 'urn:ietf:params:oauth:grant-type:device_code'

    # The on-behalf-of flow
    IMPERSONATION = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
