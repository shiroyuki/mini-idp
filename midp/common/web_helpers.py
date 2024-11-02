import asyncio
from copy import deepcopy
from typing import Dict, Any, Optional

from imagination import container
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from midp.common.env_helpers import SELF_REFERENCE_URI
from midp.common.renderer import TemplateRenderer
from midp.common.session_manager import SessionManager, Session
from midp.common.token_manager import TokenParser


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


async def restore_session(request: Request) -> Session:
    session_manager: SessionManager = container.get(SessionManager)
    session: Session = await asyncio.to_thread(session_manager.load, encrypted_id=request.cookies.get('sid'))
    return session


async def authenticate_with_local_token(request: Request) -> Dict[str, Any]:
    raw_bearer_token = request.headers.get('Authorization')
    if raw_bearer_token and raw_bearer_token.startswith('Bearer '):
        bearer_token = raw_bearer_token[len('Bearer '):]

    token_parser: TokenParser = container.get(TokenParser)
    claims: Dict[str, Any] = await asyncio.to_thread(token_parser.parse,
                                                     token=bearer_token)
    return claims
