import asyncio
from typing import List

from fastapi import APIRouter
from imagination import container
from pydantic import BaseModel, Field

from midp.common.web_helpers import make_generic_json_response, GenericResponse
from midp.config import MainConfig, restore_from_snapshot, export_snapshot

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


@recovery_router.post("/import", response_model=MainConfig, response_model_exclude_defaults=True)
async def import_from_configuration(main_config: MainConfig):
    await asyncio.to_thread(restore_from_snapshot, main_config)
    return await asyncio.to_thread(export_snapshot)


@recovery_router.post("/export", response_model=MainConfig, response_model_exclude_defaults=True)
async def export_config():
    return await asyncio.to_thread(export_snapshot)
