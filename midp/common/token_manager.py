from copy import deepcopy
from time import time
from typing import List, Any, Dict, Optional

from imagination.decorator.service import Service
from pydantic import BaseModel

from midp.common.enigma import Enigma
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicySubject
from midp.static_info import access_token_ttl, refresh_token_ttl


class TokenSet(BaseModel):
    access_claims: Dict[str, Any]
    access_token: Optional[str] = None
    refresh_claims: Dict[str, Any]
    refresh_token: Optional[str] = None


@Service()
class RootTokenManager:
    def __init__(self, enigma: Enigma):
        self._enigma = enigma

    def generate(self, access_claims: Dict[str, Any], refresh_claims: Dict[str, Any]) -> TokenSet:
        current_time = time()

        final_access_claims = deepcopy(access_claims)
        final_access_claims['exp'] = current_time + access_token_ttl

        final_refresh_claims = deepcopy(refresh_claims)
        final_refresh_claims['exp'] = current_time + refresh_token_ttl

        return TokenSet(
            access_claims=final_access_claims,
            access_token=self._enigma.encode(final_access_claims),
            refresh_claims=final_refresh_claims,
            refresh_token=self._enigma.encode(final_refresh_claims),
        )


class TokenGenerationError(RuntimeError):
    pass


@Service()
class UserTokenManager:
    def __init__(self, root_token_manager: RootTokenManager, user_dao: UserDao, policy_dao: PolicyDao,
                 client_dao: ClientDao):
        self._root_token_manager = root_token_manager
        self._user_dao = user_dao
        self._policy_dao = policy_dao
        self._client_dao = client_dao

    def generate(self,
                 subject: IAMPolicySubject,
                 resource_url: str,
                 requested_scopes: List[str]) -> TokenSet:
        subject = subject.subject

        user = self._user_dao.get(subject)

        if not user:
            raise TokenGenerationError('access_denied')

        policies = [
            p
            for p in self._policy_dao.select(
                'resource = LEFT(:resource_url, LENGTH(resource))',
                dict(resource_url=resource_url)
            )
        ]

        print(f'PANDA: policies = {policies}')

        if not policies:
            raise TokenGenerationError('access_denied')

        current_time = time()

        access_claims = dict(sub=subject,
                             scope=' '.join(requested_scopes),
                             aud=resource_url,
                             exp=current_time + access_token_ttl)
        refresh_claims = dict(sub=subject,
                              scope='openid refresh',
                              aud=resource_url,
                              exp=current_time + (access_token_ttl * 7))

        return self._root_token_manager.generate(access_claims, refresh_claims)
