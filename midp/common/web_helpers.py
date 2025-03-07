import asyncio
from copy import deepcopy
from typing import Dict, Any, Optional

from imagination import container
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from midp.common.renderer import TemplateRenderer
from midp.common.session_manager import SessionManager, Session
from midp.common.token_manager import TokenManager, InvalidTokenError
from midp.log_factory import get_logger_for

mod_logger = get_logger_for("midp.common.web_helpers")


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


class MissingBearerToken(Exception):
    pass


class InvalidBearerToken(Exception):
    pass


def retrieve_bearer_token(request: Request) -> str:
    raw_bearer_token = request.headers.get('Authorization')
    if raw_bearer_token and raw_bearer_token.startswith('Bearer '):
        token = raw_bearer_token[len('Bearer '):]
        if token and len(token) >= 20:
            return token
        else:
            raise MissingBearerToken()
    else:
        raise MissingBearerToken()


def authenticate_with_bearer_token(request: Request) -> Dict[str, Any]:
    manager: TokenManager = container.get(TokenManager)
    try:
        return manager.parse_token(retrieve_bearer_token(request))
    except MissingBearerToken as e:
        raise e
    except InvalidTokenError as e:
        raise InvalidBearerToken("missing" if isinstance(e, MissingBearerToken) else "invalid") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {type(e).__module__}.{type(e).__name__}: {e}") from e


# def current_user(request: Request) -> Optional[Dict[str, Any]]:
