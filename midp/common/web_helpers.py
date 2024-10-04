import asyncio
from copy import deepcopy
from typing import Dict, Any, Optional

from imagination import container
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from midp.common.renderer import TemplateRenderer
from midp.common.session_manager import SessionManager, Session
from midp.iam.dao.realm import RealmDao
from midp.iam.models import Realm


class GenericResponse(BaseModel):
    status: int
    summary: str
    details: Optional[Dict[str, Any]] = None


def make_generic_json_response(status: int,
                               summary: Optional[str] = None,
                               details: Optional[Dict[str, Any]] = None,
                               *,
                               headers: Optional[Dict[str, Any]] = None) -> Response:
    default_codes: Dict[int, str] = {
        200: 'ok',
        401: 'authorization_required',
        403: 'access_denied',
        404: 'not_found',
        409: 'conflict',
        410: 'gone'
    }

    response_headers = deepcopy(headers) if headers else dict()
    response_headers.update({'Content-type': 'application/json'})

    return Response(GenericResponse(status=status,
                                    summary=summary or default_codes[status],
                                    details=details).model_dump_json(),
                    status,
                    headers=response_headers)


def respond_html(template_path: str,
                 context: Optional[Dict[str, Any]] = None,
                 *,
                 status: int = 200,
                 headers: Optional[Dict[str, Any]] = None):
    response_headers = deepcopy(headers) if headers else dict()
    response_headers.update({'Content-type': 'text/html'})

    engine: TemplateRenderer = container.get(TemplateRenderer)
    return Response(engine.render(template_path, context), status, headers=response_headers)


def get_basic_template_variables(request: Request) -> Dict[str, Any]:
    return dict(
        base_url=str(request.base_url),
        url=str(request.url),
    )


async def web_path_get_realm(request: Request) -> Realm:
    realm_dao: RealmDao = container.get(RealmDao)
    realm: Realm = await asyncio.to_thread(realm_dao.get, request.path_params.get('realm_id'))

    if not realm:
        raise HTTPException(404)

    return realm


async def restore_session(request: Request) -> Session:
    session_manager: SessionManager = container.get(SessionManager)
    session: Session = await asyncio.to_thread(session_manager.load, encrypted_id=request.cookies.get('sid'))
    return session
