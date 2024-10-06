from typing import Optional, List, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RootScope(BaseModel):
    __tbl__ = 'iam_scope'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    sensitive: bool = False
    fixed: bool = False

    @classmethod
    def predefined(cls, name: str, description: Optional[str] = None, sensitive: bool = False):
        return cls(
            name=name,
            description=description,
            sensitive=sensitive,
            fixed=True,
        )


class PredefinedRootScope:
    ALL = RootScope.predefined('root:all',
                               'Manage everything')
    MANAGE_CLIENTS = RootScope.predefined('root:manage:client',
                                          'Manage only clients in the root realm (system)')
    MANAGE_USERS = RootScope.predefined('root:manage:user',
                                        'Manage only users in the root realm (system)')
    MANAGE_REALMS = RootScope.predefined('root:manage:realm',
                                         'Manage any realms')


class RootUser(BaseModel):
    __tbl__ = 'root_user'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    password: Optional[str]  # Auxiliary Property: Decrypted
    email: str
    full_name: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)  # Role URNs # Auxiliary Property: Augmented


class RootUserReadOnly(BaseModel):
    __tbl__ = 'root_user'

    id: str
    name: str
    email: str
    full_name: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)

    @classmethod
    def build_from(cls, user: RootUser):
        return cls(
            id=user.cls,
            name=user.name,
            email=user.email,
            full_name=user.full_name,
            scopes=user.scopes,
        )


class RootOAuthClient(BaseModel):
    __tbl__ = 'root_client'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    realm_id: Optional[str] = None  # Hidden Property
    name: str
    secret: Optional[str] = None  # Auxiliary Property: Decrypted
    audience: str
    grant_types: List[str]
    response_types: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)  # Scope limiter
    extras: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

