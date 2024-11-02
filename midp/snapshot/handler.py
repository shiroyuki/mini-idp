import asyncio

from fastapi import APIRouter

from midp.snapshot.utils import restore_from_snapshot, export_snapshot
from midp.snapshot.models import AppSnapshot

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


@recovery_router.post("",
                      response_model=AppSnapshot,
                      response_model_exclude_defaults=True,
                      summary='Import resources from the snapshot file')
async def import_from_snapshot(main_config: AppSnapshot):
    await asyncio.to_thread(restore_from_snapshot, main_config)
    return await asyncio.to_thread(export_snapshot)


@recovery_router.get("",
                      response_model=AppSnapshot,
                      response_model_exclude_defaults=True,
                      summary='Export a snapshot of the system')
async def generate_snapshot():
    return await asyncio.to_thread(export_snapshot)
