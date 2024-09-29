from os import getenv
import re
from typing import Annotated, Any, Dict, Optional, Union
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yaml

from midp.config import MainConfig
from midp.models import IAMPolicy, OpenIDConfiguration, Realm

load_dotenv()

realms: Dict[str, Realm] = dict()

# config_paths = re.split(r',', getenv('MINI_IDP_CONFIG_PATHS') or 'config-default.yml')
# for config_path in config_paths:
#     with open(config_path, 'r') as f:
#         raw_config = yaml.load(f.read(), Loader=yaml.BaseLoader)
#         config = MainConfig(**raw_config)
#         for realm in config.realms:
#             realms[realm.urn] = realm

app = FastAPI()


class GenericResponse(BaseModel):
    status: int
    summary: str
    details: Optional[Dict[str, Any]] = None


def _make_generic_response(status: int,
                           summary: Optional[str] = None,
                           details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    default_codes: Dict[int, str] = {
        401: 'authorization_required',
        403: 'access_denied',
        404: 'not_found',
        409: 'conflict',
        410: 'gone'
    }
    return JSONResponse(GenericResponse(status, summary or default_codes[status], details), status)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get(r'/realms/{realm_id}/.well-known/openid-configuration')
def get_realm_openid_config(realm_id: str, request: Request) -> OpenIDConfiguration:
    if realm_id in realms:
        return OpenIDConfiguration.make(str(request.base_url), realms[realm_id])
    else:
        raise HTTPException(404)


@app.post(r'/realms/{realm_id}/device')
def initiate_device_authorization(realm_id: str,
                                  client_id: Annotated[str, Form()],
                                  scope: Annotated[str, Form()],
                                  request: Request):
    requested_scopes = re.split(r'\s+', scope)

    if 'offline_access' not in requested_scopes:
        raise HTTPException(400, 'scope_missing')

    if realm_id in realms:
        realm = realms[realm_id]
        policy: Optional[IAMPolicy] = None

        for existing_policy in realm.policies:
            if existing_policy.client_id != client_id:
                continue

            if existing_policy.grant_type != 'urn:ietf:params:oauth:grant-type:device_code':
                continue

            policy = existing_policy

        if not policy:
            raise HTTPException(403)


    else:
        raise HTTPException(404)
