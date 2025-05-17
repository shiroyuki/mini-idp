from copy import deepcopy
from math import floor
from time import time
from typing import List, Any, Dict, Optional, Set

from imagination.decorator.service import Service
from jwt import ExpiredSignatureError, DecodeError
from pydantic import BaseModel

from midp.common.enigma import Enigma
from midp.common.env_helpers import SELF_REFERENCE_URI
from midp.common.policy_manager import PolicyResolver
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicySubject, IAMPolicy, IAMUser, IAMOAuthClient
from midp.log_factory import midp_logger_for
from midp.static_info import ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL


class InvalidTokenError(RuntimeError):
    pass


@Service()
class TokenParser:
    def __init__(self, enigma: Enigma):
        self._enigma = enigma

    def parse(self, token: str, audience: Optional[str] = None) -> Dict[str, Any]:
        claims: Dict[str, Any] = dict()

        try:
            claims.update(
                self._enigma.decode(token, issuer=SELF_REFERENCE_URI, audience=audience or SELF_REFERENCE_URI))
        except ExpiredSignatureError:
            raise InvalidTokenError()

        return claims


class TokenSet(BaseModel):
    access_claims: Dict[str, Any]
    access_token: Optional[str] = None
    refresh_claims: Dict[str, Any]
    refresh_token: Optional[str] = None


class TokenGenerationError(RuntimeError):
    pass


@Service()
class TokenManager:
    def __init__(self,
                 enigma: Enigma,
                 policy_resolver: PolicyResolver,
                 user_dao: UserDao,
                 policy_dao: PolicyDao,
                 client_dao: ClientDao):
        self._logger = midp_logger_for(self)
        self._enigma = enigma
        self._policy_resolver = policy_resolver
        self._user_dao = user_dao
        self._policy_dao = policy_dao
        self._client_dao = client_dao

        self._self_reference_uri = SELF_REFERENCE_URI

        if not self._self_reference_uri.endswith('/'):
            self._self_reference_uri += '/'

    def _generate_token_set(self, access_claims: Dict[str, Any], refresh_claims: Dict[str, Any]) -> TokenSet:
        current_time = time()

        final_access_claims = deepcopy(access_claims)
        final_access_claims['exp'] = current_time + ACCESS_TOKEN_TTL

        final_refresh_claims = deepcopy(refresh_claims)
        final_refresh_claims['exp'] = current_time + REFRESH_TOKEN_TTL

        return TokenSet(
            access_claims=final_access_claims,
            access_token=self._enigma.encode(final_access_claims),
            refresh_claims=final_refresh_claims,
            refresh_token=self._enigma.encode(final_refresh_claims),
        )

    def create_token_set(self,
                         subject: IAMPolicySubject,
                         resource_url: Optional[str] = None,
                         requested_scopes: Optional[List[str]] = None) -> TokenSet:
        resource_url = resource_url or self._self_reference_uri

        resolution = self._policy_resolver.evaluate(
            resource_url=resource_url,
            scopes=requested_scopes,
            subjects=[subject],
        )

        granted_scopes: Set[str] = set()
        for policy in resolution.policies:
            granted_scopes.update(policy.scopes)

        current_time = time()

        # TODO Implement JTI issuing, validation, and invalidation.
        access_claims = dict(sub=subject.subject,
                             psl=resolution.subjects,  # Policy Subject List
                             scope=' '.join(sorted(granted_scopes)),
                             iss=self._self_reference_uri,
                             aud=resource_url,
                             exp=floor(current_time + ACCESS_TOKEN_TTL))

        refresh_claims = dict(sub=subject.subject,
                              scope='openid refresh',
                              iss=self._self_reference_uri,
                              aud=resource_url,
                              exp=floor(current_time + (ACCESS_TOKEN_TTL * 7)))

        return self._generate_token_set(access_claims, refresh_claims)

    def parse_token(self, token: str, resource_url: Optional[str] = None):
        claims: Dict[str, Any] = dict()

        try:
            claims.update(
                self._enigma.decode(
                    token,
                    issuer=SELF_REFERENCE_URI,
                    audience=resource_url or SELF_REFERENCE_URI,
                )
            )
        except (DecodeError, ExpiredSignatureError) as e:
            self._logger.error(f"Unable to parse this token: {token}")
            message = f"Unexpected error while parsing {token}"
            if isinstance(e, ExpiredSignatureError):
                message = 'Token expired'
            elif isinstance(e, DecodeError):
                message = 'Token decode error'
            raise InvalidTokenError(message) from e

        return claims
