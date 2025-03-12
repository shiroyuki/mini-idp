import asyncio
from typing import Optional

from imagination.decorator.service import Service

from midp.iam.dao.client import ClientDao
from midp.iam.models import IAMOAuthClient
from midp.log_factory import get_logger_for_object
from midp.models import GrantType


class ClientAuthenticationError(RuntimeError):
    def __init__(self, reason):
        super().__init__(reason)

    @property
    def reason(self):
        return self.args[0]


@Service()
class ClientAuthenticator:
    def __init__(self, client_dao: ClientDao):
        self._log = get_logger_for_object(self)
        self._client_dao = client_dao

    async def authenticate(self,
                           /,
                           client_id: str,
                           grant_type: str,
                           client_secret: Optional[str] = None,
                           ) -> IAMOAuthClient:
        client_dao: ClientDao = self._client_dao
        client: IAMOAuthClient = await asyncio.to_thread(client_dao.get, client_id)

        if not client:
            self._log.warning(f'Unable to find Client/{client_id} for any grant types.')
            raise ClientAuthenticationError('invalid_client')

        if grant_type == GrantType.CLIENT_CREDENTIALS and (client.name != client_id or client.secret != client_secret):
            self._log.warning(f'Found Client/{client_id} but the given secret is mismatched.')
            raise ClientAuthenticationError('invalid_client')

        if grant_type not in client.grant_types:
            self._log.warning(f'Found Client/{client_id} but it does not have GrantType/{grant_type}.')
            raise ClientAuthenticationError('unauthorized_client')

        return client  # No code means OK.
