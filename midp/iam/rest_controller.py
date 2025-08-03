from typing import Annotated, Dict, Any

from fastapi import Depends
from imagination.decorator.service import Service
from starlette.requests import Request

from midp.common.base_rest_controller import BaseRestController
from midp.common.web_helpers import authenticate_with_bearer_token
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicy, IAMOAuthClient, IAMRole, IAMScope, IAMUser


@Service()
class PolicyRestController(BaseRestController[IAMPolicy]):
    def __init__(self, dao: PolicyDao):
        super().__init__(dao)
        self._dao = dao

    def _get_scopes_namespace(self) -> str:
        return 'idp.policy'

    def create(self, request: Request, obj: IAMPolicy, access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> IAMPolicy:
        return super().create(request, obj, access_claims)


@Service()
class ClientRestController(BaseRestController[IAMOAuthClient]):
    def __init__(self, dao: ClientDao):
        super().__init__(dao)
        self._dao = dao

    def _get_scopes_namespace(self) -> str:
        return 'idp.client'

    def create(self, request: Request, obj: IAMOAuthClient, access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> IAMOAuthClient:
        return super().create(request, obj, access_claims)


@Service()
class RoleRestController(BaseRestController[IAMRole]):
    def __init__(self, dao: RoleDao):
        super().__init__(dao)
        self._dao = dao

    def _get_scopes_namespace(self) -> str:
        return 'idp.role'

    def create(self, request: Request, obj: IAMRole, access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> IAMRole:
        return super().create(request, obj, access_claims)


@Service()
class ScopeRestController(BaseRestController[IAMScope]):
    def __init__(self, dao: ScopeDao):
        super().__init__(dao)
        self._dao = dao

    def _get_scopes_namespace(self) -> str:
        return 'idp.scope'

    def create(self, request: Request, obj: IAMScope, access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> IAMScope:
        return super().create(request, obj, access_claims)


@Service()
class UserRestController(BaseRestController[IAMUser]):
    def __init__(self, dao: UserDao):
        super().__init__(dao)
        self._dao = dao

    def _get_scopes_namespace(self) -> str:
        return 'idp.user'

    def _hide_sensitive_fields(self, obj: IAMUser) -> IAMUser:
        return obj.model_copy(update={"password": None}, deep=False)

    def create(self, request: Request, obj: IAMUser, access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> IAMUser:
        return super().create(request, obj, access_claims)
