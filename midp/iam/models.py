from enum import Enum
from typing import Any, Dict, List, Optional, Iterable
from uuid import uuid4
from pydantic import BaseModel, Field

from midp.common.env_helpers import SELF_REFERENCE_URI


class IAMScope(BaseModel):
    __tbl__ = 'iam_scope'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    sensitive: Optional[bool] = False
    fixed: Optional[bool] = False

    @classmethod
    def predefined(cls, name: str, description: Optional[str] = None, sensitive: bool = False):
        return cls(
            name=name,
            description=description,
            sensitive=sensitive,
            fixed=True,
        )


class PredefinedScope(Enum):
    OPENID = IAMScope.predefined('openid', 'OpenID Connect')
    PROFILE = IAMScope.predefined('profile', 'Profile')
    EMAIL = IAMScope.predefined('email', 'E-mail Address')
    OFFLINE_ACCESS = IAMScope.predefined('offline_access', 'Offline Access', sensitive=True)  # for the device-code flow

    # Non-standard scopes
    IMPERSONATION = IAMScope.predefined('user.impersonation',
                                        'Read Access to User Profile')  # for an OAuth2 to impersonate as a user

    # Mini IDP Management Scopes
    IDP_ROOT = IAMScope.predefined('idp.root', 'IDP Root Administrator')
    IDP_ADMIN = IAMScope.predefined('idp.admin', 'IDP Administrator')

    # Mini IDP Resource Scopes
    IAM_CLIENT_LIST = IAMScope.predefined('idp.client.list', 'List OAuth clients')
    IAM_CLIENT_READ = IAMScope.predefined('idp.client.read', 'Read OAuth clients')
    IAM_CLIENT_WRITE = IAMScope.predefined('idp.client.write', 'Read OAuth clients', sensitive=True)
    IAM_CLIENT_DELETE = IAMScope.predefined('idp.client.delete', 'Delete OAuth clients', sensitive=True)
    IAM_POLICY_LIST = IAMScope.predefined('idp.policy.list', 'List IAM policies')
    IAM_POLICY_READ = IAMScope.predefined('idp.policy.read', 'Read IAM policies')
    IAM_POLICY_WRITE = IAMScope.predefined('idp.policy.write', 'Read IAM policies', sensitive=True)
    IAM_POLICY_DELETE = IAMScope.predefined('idp.policy.delete', 'Delete IAM policies', sensitive=True)
    IAM_ROLE_LIST = IAMScope.predefined('idp.role.list', 'List IAM roles')
    IAM_ROLE_READ = IAMScope.predefined('idp.role.read', 'Read IAM roles')
    IAM_ROLE_WRITE = IAMScope.predefined('idp.role.write', 'Read IAM roles', sensitive=True)
    IAM_ROLE_DELETE = IAMScope.predefined('idp.role.delete', 'Delete IAM roles', sensitive=True)
    IAM_SCOPE_LIST = IAMScope.predefined('idp.scope.list', 'List IAM scopes')
    IAM_SCOPE_READ = IAMScope.predefined('idp.scope.read', 'Read IAM scopes')
    IAM_SCOPE_WRITE = IAMScope.predefined('idp.scope.write', 'Read IAM scopes', sensitive=True)
    IAM_SCOPE_DELETE = IAMScope.predefined('idp.scope.delete', 'Delete IAM scopes', sensitive=True)
    IAM_USER_LIST = IAMScope.predefined('idp.user.list', 'List IAM users')
    IAM_USER_READ = IAMScope.predefined('idp.user.read', 'Read IAM users')
    IAM_USER_WRITE = IAMScope.predefined('idp.user.write', 'Write IAM users', sensitive=True)
    IAM_USER_DELETE = IAMScope.predefined('idp.user.delete', 'Delete IAM users', sensitive=True)


COMMON_SCOPES = [
    PredefinedScope.OPENID.value,
    PredefinedScope.PROFILE.value,

    PredefinedScope.IAM_CLIENT_LIST.value,
    PredefinedScope.IAM_CLIENT_READ.value,

    PredefinedScope.IAM_POLICY_LIST.value,
    PredefinedScope.IAM_POLICY_READ.value,

    PredefinedScope.IAM_ROLE_LIST.value,
    PredefinedScope.IAM_ROLE_READ.value,

    PredefinedScope.IAM_SCOPE_LIST.value,
    PredefinedScope.IAM_SCOPE_READ.value,

    PredefinedScope.IAM_USER_LIST.value,
    PredefinedScope.IAM_USER_READ.value,
]

ADMIN_SCOPES = [
    PredefinedScope.IDP_ADMIN.value,

    PredefinedScope.IAM_CLIENT_DELETE.value,
    # The user requires the write permission to read the sensitive information.
    PredefinedScope.IAM_CLIENT_WRITE.value,

    PredefinedScope.IAM_POLICY_DELETE.value,
    PredefinedScope.IAM_POLICY_WRITE.value,

    PredefinedScope.IAM_ROLE_DELETE.value,
    PredefinedScope.IAM_ROLE_WRITE.value,

    PredefinedScope.IAM_SCOPE_DELETE.value,
    PredefinedScope.IAM_SCOPE_WRITE.value,

    PredefinedScope.IAM_USER_DELETE.value,
    # The user requires the write permission to read the sensitive information.
    PredefinedScope.IAM_USER_WRITE.value,
]


class IAMRole(BaseModel):
    __tbl__ = 'iam_role'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    fixed: Optional[bool] = False


class PredefinedRole(Enum):
    IDP_ROOT = IAMRole(name='idp.root', description='IDP Owner', fixed=True)
    IDP_ADMIN = IAMRole(name='idp.admin', description='IDP Admin', fixed=True)
    IDP_USER = IAMRole(name='idp.user', description='IDP User', fixed=True)


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


class GrantType:
    # The authorization flow
    AUTHORIZATION = 'authorization'

    # The client-credentials flow
    CLIENT_CREDENTIALS = 'client_credentials'

    # The device-code flow
    DEVICE_CODE = 'urn:ietf:params:oauth:grant-type:device_code'

    # The on-behalf-of flow
    IMPERSONATION = 'urn:ietf:params:oauth:grant-type:jwt-bearer'


KNOWN_GRANT_TYPES = [
    GrantType.AUTHORIZATION,
    GrantType.CLIENT_CREDENTIALS,
    GrantType.DEVICE_CODE,
    GrantType.IMPERSONATION,
]

KNOWN_RESPONSE_TYPES = ["code"]


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
    fixed: Optional[bool] = False


class PredefinedPolicy(Enum):
    IDP_ROOT_POLICY = IAMPolicy(
        name='idp.root',
        resource=SELF_REFERENCE_URI,
        subjects=[IAMPolicySubject(kind='role', subject=PredefinedRole.IDP_ROOT.value.name)],
        scopes=[scope.name for scope in COMMON_SCOPES + ADMIN_SCOPES + [PredefinedScope.IDP_ROOT.value]],
        fixed=True,
    )

    IDP_ADMIN_POLICY = IAMPolicy(
        name='idp.admins',
        resource=SELF_REFERENCE_URI,
        subjects=[IAMPolicySubject(kind='role', subject=PredefinedRole.IDP_ADMIN.value.name)],
        scopes=[scope.name for scope in COMMON_SCOPES + ADMIN_SCOPES],
        fixed=True,
    )

    IDP_USER_POLICY = IAMPolicy(
        name='idp.users',
        resource=SELF_REFERENCE_URI,
        subjects=[IAMPolicySubject(kind='role', subject=PredefinedRole.IDP_USER.value.name)],
        scopes=[scope.name for scope in COMMON_SCOPES],
        fixed=True,
    )
