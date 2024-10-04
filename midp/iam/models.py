from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin
from uuid import uuid4
from pydantic import BaseModel, Field


class GrantType:
    # The authorization flow
    AUTHORIZATION = 'authorization'

    # The client-credentials flow
    CLIENT_CREDENTIALS = 'client_credentials'

    # The device-code flow
    DEVICE_CODE = 'urn:ietf:params:oauth:grant-type:device_code'

    # The on-behalf-of flow
    IMPERSONATION = 'urn:ietf:params:oauth:grant-type:jwt-bearer'


class IAMScope(BaseModel):
    __tbl__ = 'iam_scope'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    realm_id: Optional[str] = None  # Hidden Property
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

    ROOT_ADMIN = IAMScope.predefined('root:admin', 'Root Administrator')  # for direct access to all APIs for all realms
    REALM_ADMIN = IAMScope.predefined('realm:admin',
                                      'Realm Administrator')  # for direct access to all APIs for one specific realm
    USER_READ = IAMScope.predefined('user.read',
                                    'Read Access to User Profile')  # for an OAuth2 to impersonate as a user


PREDEFINED_SCOPES = [getattr(PredefinedScope, p_name)
                     for p_name in dir(PredefinedScope)
                     if p_name[0] != '_' and isinstance(getattr(PredefinedScope, p_name), IAMScope)]
PREDEFINED_SCOPE_NAMES = [s.name for s in PREDEFINED_SCOPES]


class IAMRole(BaseModel):
    __tbl__ = 'iam_role'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    realm_id: Optional[str] = None  # Hidden Property
    name: str
    description: Optional[str] = None


class IAMUser(BaseModel):
    __tbl__ = 'iam_user'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    realm_id: Optional[str] = None  # Hidden Property
    name: str
    password: Optional[str]  # Auxiliary Property: Decrypted
    email: str
    full_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)  # Role URNs # Auxiliary Property: Augmented


class ReadOnlyIAMUser(BaseModel):
    id: str = None
    realm_id: Optional[str] = None  # Hidden Property
    name: str
    email: str
    full_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)  # Role URNs # Auxiliary Property: Augmented

    @classmethod
    def build_from(cls, user: IAMUser):
        return cls(
            id=user.id,
            realm_id=user.realm_id,
            name=user.name,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
        )


class OAuthClient(BaseModel):
    __tbl__ = 'client'

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


class IAMPolicySubject(BaseModel):
    subject: str  # ID or name
    kind: str = Field(pattern=r'client|user|role')


class IAMPolicy(BaseModel):
    __tbl__ = 'iam_policy'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    realm_id: Optional[str] = None  # Hidden Property
    resource: str
    subjects: List[IAMPolicySubject]
    scopes: List[str]


class Realm(BaseModel):
    __tbl__ = 'realm'

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    name: str
    scopes: List[IAMScope] = Field(default_factory=list)  # Auxiliary Property: Augmented
    roles: List[IAMRole] = Field(default_factory=list)  # Auxiliary Property: Augmented
    users: List[IAMUser] = Field(default_factory=list)  # Auxiliary Property: Augmented
    clients: List[OAuthClient] = Field(default_factory=list)  # Auxiliary Property: Augmented
    policies: List[IAMPolicy] = Field(default_factory=list)  # Auxiliary Property: Augmented


class OpenIDConfiguration(BaseModel):
    issuer: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    device_authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    introspection_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    end_session_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    grant_types_supported: Optional[List[str]] = None
    response_types_supported: Optional[List[str]] = None
    scopes_supported: Optional[List[str]] = None

    @classmethod
    def make(cls, base_url: str, realm: Realm):
        realm_base_url = urljoin(base_url, f'realms/{realm.name}/')

        scopes: Set[str] = set()
        for policy in realm.policies:
            scopes.update(policy.scopes)

        return cls(
            issuer=realm_base_url,
            authorization_endpoint=None,  # urljoin(realm_base_url, f'auth'),
            device_authorization_endpoint=urljoin(realm_base_url, f'device'),
            token_endpoint=urljoin(realm_base_url, f'token'),
            introspection_endpoint=None,  # urljoin(realm_base_url, f'introspection'),
            userinfo_endpoint=None,  # urljoin(realm_base_url, f'userinfo'),
            end_session_endpoint=None,  # urljoin(realm_base_url, f'logout'),
            jwks_uri=None,  # urljoin(realm_base_url, f'certs'),
            grant_types_supported=sorted({policy.grant_type for policy in realm.policies}),
            response_types_supported=sorted({policy.response_type for policy in realm.policies}),
            scopes_supported=sorted(scopes),
        )
