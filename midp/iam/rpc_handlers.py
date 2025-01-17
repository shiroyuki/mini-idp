from typing import Annotated, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from imagination import container
from starlette.responses import Response

from midp.common.web_helpers import authenticate_with_local_token
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMUserReadOnly

iam_rpc_router = APIRouter(prefix='/rpc/iam', tags=['rpc:iam'])


@iam_rpc_router.get('/self/profile')
def get_user_profile(response: Response, claims: Annotated[Dict[str, Any], Depends(authenticate_with_local_token)]) -> Optional[IAMUserReadOnly]:
    user_id = claims['sub']
    user_dao: UserDao = container.get(UserDao)
    user = user_dao.get(user_id)
    if user is None:
        raise HTTPException(status_code=404)
    else:
        return IAMUserReadOnly.build_from(user)
