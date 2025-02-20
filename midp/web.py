import asyncio
from urllib.parse import urljoin

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from midp import static_info
from midp.common.env_helpers import optional_env
from midp.common.token_manager import InvalidTokenError
from midp.log_factory import get_logger_for
from midp.oauth.handler import oauth_router
from midp.oauth.models import OpenIDConfiguration
from midp.snapshot.handler import recovery_router
from midp.iam.handlers import iam_rest_routers
from midp.iam.rpc_handlers import iam_rpc_router

app = FastAPI(title=static_info.ARTIFACT_ID, version=static_info.VERSION)
log = get_logger_for('root:web')

MINI_IDP_DEV_PERMANENT_DELAY = float(optional_env('MINI_IDP_DEV_PERMANENT_DELAY',
                                                  '0',
                                                  'Permanent connection delay for development and testing'))

API_PREFIX_PATHS = {'/api', '/rest', '/rpc'}

@app.middleware('security')
async def intercept_request_response(request: Request, call_next):
    log_prefix = f'{request.method} {request.url}'
    request_path = request.url.path

    # Enforce the permanent delay
    if (
            MINI_IDP_DEV_PERMANENT_DELAY > 0
            and sum([1 if request_path.startswith(p) else 0 for p in API_PREFIX_PATHS]) > 0
    ):
        log.debug(f'{log_prefix}: Pause the request...')
        await asyncio.sleep(MINI_IDP_DEV_PERMANENT_DELAY)
        log.debug(f'{log_prefix}: Resume the request.')

    # Proceed with the request.
    try:
        response: Response = await call_next(request)
    except InvalidTokenError:
        response = Response(status_code=401)
    response.headers['Server'] = f'{static_info.ARTIFACT_ID}/{static_info.VERSION}'

    return response


@app.get("/service-info", tags=['app-metadata'])
def release_information():
    app_name = optional_env("APP_NAME", static_info.DEFAULT_APP_NAME)
    if app_name == static_info.DEFAULT_APP_NAME:
        log.warning("The default app name is used. If you would like to customize "
                    "the name of the app/deployment, please set APP_NAME.")
    return {
        "deployment": {"name": app_name},
        "release": {
            "artifact": static_info.ARTIFACT_ID,
            "version": static_info.VERSION,
        }
    }


@app.get(r'/.well-known/openid-configuration',
         response_model_exclude_defaults=True,
         tags=['oauth'],
         summary='The OpenID Configuration of this Service')
async def get_openid_configuration(request: Request) -> OpenIDConfiguration:
    base_url = str(request.base_url)

    return OpenIDConfiguration.make(urljoin(base_url, 'oauth/'))


@app.post(r'/rpc/inquiry')
async def run_inquiry(request: Request) -> Response:
    return Response('Not yet implemented', status_code=501)


app.include_router(oauth_router)
app.include_router(recovery_router)
[app.include_router(router) for router in iam_rest_routers]
app.include_router(iam_rpc_router)

app.mount("/public",
          StaticFiles(directory=static_info.PUBLIC_FILE_PATH, html=True),
          name="web_public")

app.mount("/",
          StaticFiles(directory=static_info.WEB_FRONTEND_FILE_PATH, html=True),
          name="web_ui")

FastAPIInstrumentor.instrument_app(app)
