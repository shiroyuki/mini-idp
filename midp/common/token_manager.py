from copy import deepcopy
from math import floor
from time import time
from typing import List, Any, Dict, Optional

from imagination.decorator.service import Service
from pydantic import BaseModel

from midp.common.enigma import Enigma
from midp.common.env_helpers import SELF_REFERENCE_URI
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicySubject, IAMPolicy, IAMUser
from midp.static_info import ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL


@Service()
class TokenParser:
    def __init__(self, enigma: Enigma):
        self._enigma = enigma

    def parse(self, token: str, audience: Optional[str] = None) -> Dict[str, Any]:
        claims: Dict[str, Any] = dict()
        claims.update(self._enigma.decode(token, issuer=SELF_REFERENCE_URI, audience=audience or SELF_REFERENCE_URI))

        return claims


class TokenSet(BaseModel):
    access_claims: Dict[str, Any]
    access_token: Optional[str] = None
    refresh_claims: Dict[str, Any]
    refresh_token: Optional[str] = None


@Service()
class GeneralTokenGenerator:
    def __init__(self, enigma: Enigma):
        self._enigma = enigma

    def generate(self, access_claims: Dict[str, Any], refresh_claims: Dict[str, Any]) -> TokenSet:
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


class TokenGenerationError(RuntimeError):
    pass


@Service()
class PrivilegeTokenGenerator:
    def __init__(self, root_token_manager: GeneralTokenGenerator, user_dao: UserDao, policy_dao: PolicyDao,
                 client_dao: ClientDao):
        self._root_token_manager = root_token_manager
        self._user_dao = user_dao
        self._policy_dao = policy_dao
        self._client_dao = client_dao

        self._self_reference_uri = SELF_REFERENCE_URI

        if not self._self_reference_uri.endswith('/'):
            self._self_reference_uri += '/'

    def generate(self,
                 subject: IAMPolicySubject,
                 resource_url: Optional[str] = None,
                 requested_scopes: Optional[List[str]] = None) -> TokenSet:
        user: Optional[IAMUser] = None

        if subject.kind == 'service':
            raise NotImplementedError('To be implemented')
        else:  # kind = 'user'
            user = self._user_dao.get(subject.subject)

            if not user:
                raise TokenGenerationError('access_denied')

            print(f'PANDA: user = {user}')

        subject_id: str = user.id

        resource_url = resource_url or self._self_reference_uri
        requested_scopes = requested_scopes or []

        if resource_url.endswith('/'):
            # When the resource URL ends with "/", we will look for all policies tied
            # to a resource URL starting with the given resource URL.
            policy_iterator = self._policy_dao.select(
                "resource LIKE :resource_url",
                dict(resource_url=resource_url + r'%'),
            )
        else:
            # When the trailing slash ("/") is not in the resource URL, this is a specific resource only.
            policy_iterator = self._policy_dao.select(
                "resource = :resource_url",
                dict(resource_url=resource_url),
            )

        policies_filtered_by_resource_url = [p for p in policy_iterator]

        print(f'PANDA: policies_filtered_by_resource_url = {policies_filtered_by_resource_url}')

        policies: List[IAMPolicy] = []

        for policy in policies_filtered_by_resource_url:
            for policy_subject in policy.subjects:
                if user:
                    if (
                            (policy_subject.kind == 'user' and policy_subject.subject == user.email)
                            or (policy_subject.kind == 'role' and policy_subject.subject in user.roles)
                    ):
                        policies.append(policy)
                else:
                    raise NotImplementedError()
                ...

        print(f'PANDA: policies = {policies}')

        if not policies:
            raise TokenGenerationError('access_denied')

        current_time = time()

        access_claims = dict(sub=subject_id,
                             roles=user.roles,
                             # TODO provide all requested scopes from the policy.
                             scope=' '.join(requested_scopes),
                             iss=self._self_reference_uri,
                             aud=resource_url,
                             exp=floor(current_time + ACCESS_TOKEN_TTL))

        refresh_claims = dict(sub=subject_id,
                              scope='openid refresh',
                              iss=self._self_reference_uri,
                              aud=resource_url,
                              exp=floor(current_time + (ACCESS_TOKEN_TTL * 7)))

        return self._root_token_manager.generate(access_claims, refresh_claims)
