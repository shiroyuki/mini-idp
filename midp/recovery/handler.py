import asyncio
from typing import List

from fastapi import APIRouter
from imagination import container
from pydantic import BaseModel, Field

from midp.common.web_helpers import make_generic_json_response, GenericResponse
from midp.config import MainConfig, restore_from_snapshot, export_snapshot
from midp.iam.dao.realm import RealmDao

recovery_router = APIRouter(
    prefix=r'/rpc/recovery',
    tags=['recover'],
    responses={
        401: dict(error='not-authenticated'),
        403: dict(error='access-denied'),
        404: dict(error='not-found'),
        405: dict(error='method-not-allowed'),
    }
)


@recovery_router.post("/import", response_model=GenericResponse, response_model_exclude_defaults=True)
async def import_from_configuration(main_config: MainConfig):
    await asyncio.to_thread(restore_from_snapshot, main_config)

    realm_dao: RealmDao = container.get(RealmDao)
    realms = [
        realm
        for realm in await asyncio.to_thread(
            realm_dao.select,
            'name IN :names',
            dict(names=tuple([r.name for r in main_config.realms]))
        )
    ]

    return make_generic_json_response(
        200,
        details={'realms': realms}
    )


class ExportRequest(BaseModel):
    realms: List[str] = Field(description='The list of realm IDs (UUIDs) or names')


@recovery_router.post("/export", response_model_exclude_defaults=True)
async def export_realms(export_request: ExportRequest):
    return await asyncio.to_thread(export_snapshot, export_request.realms)
