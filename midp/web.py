from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from midp import static_info
from midp.oauth.handler import oauth_router
from midp.recovery.handler import recovery_router
from midp.rest.handlers import rest_realm_router, rest_client_router, rest_policy_router, rest_role_router, \
    rest_scope_router, rest_user_router

app = FastAPI(title=static_info.name, version=static_info.version)


@app.middleware('security')
async def intercept_request_response(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers['X-Server'] = f'{static_info.name}/{static_info.version}'

    return response


@app.get("/service-info", tags=['app-metadata'])
def release_information():
    return {"app": static_info.name, "version": static_info.version}


@app.get("/ping")
def release_information():
    return Response('', status_code=200, headers={'Content-type': 'text/plain'})


app.include_router(oauth_router)
app.include_router(recovery_router)
app.include_router(rest_client_router)
app.include_router(rest_policy_router)
app.include_router(rest_realm_router)
app.include_router(rest_role_router)
app.include_router(rest_scope_router)
app.include_router(rest_user_router)

# TODO Deprecate this for React app
app.mount("/public",
          StaticFiles(directory=static_info.static_file_path),
          name="static")

app.mount("/",
          StaticFiles(directory=static_info.web_ui_file_path, html=True),
          name="ui")
