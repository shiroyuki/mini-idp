import asyncio
from typing import Optional

from imagination.decorator.service import Service

from midp.iam.dao.client import ClientDao
from midp.iam.models import IAMOAuthClient


@Service()
class AccessEvaluator:
    def __init__(self, client_dao: ClientDao):
        self._client_dao = client_dao

    async def check_if_client_is_allowed(self, client_id: str, grant_type: str) -> Optional[str]:
        client_dao: ClientDao = self._client_dao
        client: IAMOAuthClient = await asyncio.to_thread(client_dao.get, client_id)

        if not client:
            return 'invalid_client'

        if grant_type not in client.grant_types:
            return 'unauthorized_client'

        return None  # No code means OK.
