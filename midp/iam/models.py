from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class IAMScope(BaseModel):
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


class PredefinedScope:
    OPENID = IAMScope.predefined('openid', 'OpenID Connect')
    PROFILE = IAMScope.predefined('profile', 'Profile')
    EMAIL = IAMScope.predefined('email', 'E-mail Address')
    OFFLINE_ACCESS = IAMScope.predefined('offline_access', 'Offline Access', sensitive=True)  # for the device-code flow

    # Non-standard scopes
    SYS_ADMIN = IAMScope.predefined('system.admin',
                                      'Realm Administrator')  # for direct access to all APIs for one specific realm
    IMPERSONATION = IAMScope.predefined('user.impersonation',
                                    'Read Access to User Profile')  # for an OAuth2 to impersonate as a user


PREDEFINED_SCOPES = [getattr(PredefinedScope, p_name)
                     for p_name in dir(PredefinedScope)
                     if p_name[0] != '_' and isinstance(getattr(PredefinedScope, p_name), IAMScope)]
PREDEFINED_SCOPE_NAMES = [s.name for s in PREDEFINED_SCOPES]


class IAMRole(BaseModel):
    __tbl__ = 'iam_role'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None


IDP_OWNER = IAMRole(name='idp.owner')
IDP_ADMIN = IAMRole(name='idp.admin')
IDP_USER = IAMRole(name='idp.user')


class IAMUser(BaseModel):
    __tbl__ = 'iam_user'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    password: Optional[str]  # Auxiliary Property: Decrypted
    email: str
    full_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)  # Role URNs # Auxiliary Property: Augmented


class IAMUserReadOnly(BaseModel):
    id: str = None
    name: str
    email: str
    full_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)  # Role URNs # Auxiliary Property: Augmented

    @classmethod
    def build_from(cls, user: IAMUser):
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
        )


class IAMOAuthClient(BaseModel):
    __tbl__ = 'iam_client'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    secret: Optional[str] = None  # Auxiliary Property: Decrypted
    audience: str
    grant_types: List[str]
    response_types: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)  # Scope limiter
    extras: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class IAMOAuthClientReadOnly(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    audience: str
    grant_types: List[str]
    response_types: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)  # Scope limiter
    extras: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

    @classmethod
    def build_from(cls, client: IAMOAuthClient):
        return cls(
            id=client.id,
            name=client.name,
            audience=client.audience,
            grant_types=client.grant_types,
            response_types=client.response_types,
            scopes=client.scopes,
            extras=client.extras,
            description=client.description,
        )


class IAMPolicySubject(BaseModel):
    subject: str  # ID or name
    kind: str = Field(pattern=r'client|user|role')


class IAMPolicy(BaseModel):
    __tbl__ = 'iam_policy'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    resource: str
    subjects: List[IAMPolicySubject]
    scopes: List[str]
