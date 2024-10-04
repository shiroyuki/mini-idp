import asyncio
from typing import Optional

from fastapi import HTTPException
from imagination.decorator.service import Service

from midp.iam.dao.client import ClientDao
from midp.iam.dao.realm import RealmDao
from midp.iam.models import OAuthClient


@Service()
class AccessEvaluator:
    def __init__(self, realm_dao: RealmDao, client_dao: ClientDao):
        self._realm_dao = realm_dao
        self._client_dao = client_dao

    async def check_if_client_is_allowed(self, realm_id: str, client_id: str, grant_type: str) -> Optional[str]:
        realm_dao: RealmDao = self._realm_dao
        realm = await asyncio.to_thread(realm_dao.get, realm_id)

        if not realm:
            raise HTTPException(404)

        client_dao: ClientDao = self._client_dao
        client: OAuthClient = await asyncio.to_thread(
            client_dao.select_one,
            ' AND '.join([
                'realm_id = :realm_id',
                '(id = :client_id OR name = :client_id)',
            ]),
            dict(
                realm_id=realm.id,
                client_id=client_id,
            )
        )

        if not client:
            return 'invalid_client'

        if grant_type not in client.grant_types:
            return 'unauthorized_client'

        return None  # No code means OK.
