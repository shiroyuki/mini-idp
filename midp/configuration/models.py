from typing import List

from pydantic import BaseModel, Field

from midp.iam.models import IAMScope, IAMRole, IAMUser, IAMOAuthClient, IAMPolicy


class AppSnapshot(BaseModel):
    version: str = Field(default='1.0.0')
    scopes: List[IAMScope] = Field(default_factory=list)  # Auxiliary Property: Augmented
    roles: List[IAMRole] = Field(default_factory=list)  # Auxiliary Property: Augmented
    users: List[IAMUser] = Field(default_factory=list)  # Auxiliary Property: Augmented
    clients: List[IAMOAuthClient] = Field(default_factory=list)  # Auxiliary Property: Augmented
    policies: List[IAMPolicy] = Field(default_factory=list)  # Auxiliary Property: Augmented
