import asyncio
from typing import Optional

from imagination.decorator.service import Service

from midp.iam.dao.client import ClientDao
from midp.iam.models import IAMOAuthClient
from midp.log_factory import get_logger_for_object


@Service()
class AccessEvaluator:
    def __init__(self, client_dao: ClientDao):
        self._log = get_logger_for_object(self)
        self._client_dao = client_dao

    async def check_if_client_is_allowed(self, client_id: str, grant_type: str) -> Optional[str]:
        client_dao: ClientDao = self._client_dao
        client: IAMOAuthClient = await asyncio.to_thread(client_dao.get, client_id)

        if not client:
            self._log.warning(f'Unable to find {client_id} for any grant types')
            return 'invalid_client'

        if grant_type not in client.grant_types:
            self._log.warning(f'Unable to find {client_id} with {grant_type}')
            return 'unauthorized_client'

        return None  # No code means OK.
