import re
from enum import StrEnum
from typing import TypeVar, Generic, List, Optional, Union, Any, Dict, Annotated, Set

from fastapi import HTTPException, Depends
from imagination import container
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from midp.common.obj_patcher import PatchOperation, apply_changes
from midp.common.token_manager import TokenManager
from midp.common.web_helpers import make_generic_json_response, authenticate_with_bearer_token
from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import PredefinedScope
from midp.log_factory import get_logger_for_object

T = TypeVar('T')


class FailedResponse(BaseModel):
    error: str
    error_description: Optional[str] = None


class DataAction(StrEnum):
    LIST = 'list'
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'


class BaseRestController(Generic[T]):
    _privilege_scopes: Set[str] = set([s.value.name for s in [PredefinedScope.IDP_ROOT, PredefinedScope.IDP_ADMIN]])
    _dao: AtomicDao[T]

    def __init__(self, dao: AtomicDao[T]):
        self._log = get_logger_for_object(self)
        self._token_manager: TokenManager = container.get(TokenManager)

    def _respond_with_error(self, status: int, error: str, error_description: Optional[str] = None):
        return Response(
            status_code=status,
            content=FailedResponse(
                error=error,
                error_description=error_description
            ).model_dump_json(indent=2)
        )

    def _get_scopes_namespace(self) -> str:
        raise NotImplementedError()

    def _get_scopes_for_list(self) -> Set[str]:
        return {f'{self._get_scopes_namespace()}.list'}

    def _get_scopes_for_read(self) -> Set[str]:
        return {f'{self._get_scopes_namespace()}.read'}

    def _get_scopes_for_write(self) -> Set[str]:
        return {f'{self._get_scopes_namespace()}.write'}

    def _get_scopes_for_delete(self) -> Set[str]:
        return {f'{self._get_scopes_namespace()}.delete'}

    def _extract_scopes(self, access_claims: Dict[str, Any]) -> List[str]:
        raw_scopes = access_claims.get('scope')
        return re.split(r'\s*,\s*', raw_scopes) if raw_scopes else []

    def _check_authorization(self, action: DataAction, access_claims: Dict[str, Any]) -> bool:
        given_scopes: List[str] = self._extract_scopes(access_claims)

        if PredefinedScope.IDP_ROOT.value.name in given_scopes or PredefinedScope.IDP_ADMIN.value.name in given_scopes:
            return True

        if action == DataAction.LIST:
            required_scopes = self._get_scopes_for_list()
            matched_scopes = required_scopes.intersection(given_scopes)
        elif action == DataAction.READ:
            required_scopes = self._get_scopes_for_read()
            matched_scopes = required_scopes.intersection(given_scopes)
        elif action == DataAction.WRITE:
            required_scopes = self._get_scopes_for_write()
            matched_scopes = required_scopes.intersection(given_scopes)
        elif action == DataAction.DELETE:
            required_scopes = self._get_scopes_for_delete()
            matched_scopes = required_scopes.intersection(given_scopes)
        else:
            raise NotImplementedError('Unsupported action')

        if len(matched_scopes) == len(given_scopes):
            return True
        else:
            return False

    def list(self,
             request: Request,
             access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> List[T]:
        """ List resources """
        if not self._check_authorization(DataAction.LIST, access_claims=access_claims):
            # noinspection PyTypeChecker
            return self._respond_with_error(403, 'access.denied')

        result = [i for i in self._dao.select(order_by=[('name', 'ASC')])]
        return result if self._full_access_requested(request, access_claims) else self._hide_sensitive_fields_in_list(result)

    def create(self,
               request: Request,
               obj: T,
               access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> T:
        """ Create a new resource """
        if not self._check_authorization(DataAction.WRITE, access_claims=access_claims):
            return self._respond_with_error(403, 'access.denied')

        result = self._dao.add(obj)
        return result if self._full_access_requested(request, access_claims) else self._hide_sensitive_fields(result)

    def get(self,
            request: Request,
            id: str,
            access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]
            ) -> Union[T, FailedResponse]:
        """ Get the resource by ID """
        if not self._check_authorization(DataAction.READ, access_claims=access_claims):
            return self._respond_with_error(403, 'access.denied')

        result = self._dao.select_one('id = :id_or_name OR name = :id_or_name',
                                      dict(id_or_name=id))
        if not result:
            return self._respond_with_error(status=404, error='not-found')
        else:
            return result if self._full_access_requested(request, access_claims) else self._hide_sensitive_fields(result)

    def patch(self,
              request: Request,
              id: str,
              operations: List[PatchOperation],
              access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]
              ) -> Union[T, FailedResponse]:
        if not self._check_authorization(DataAction.WRITE, access_claims=access_claims):
            return self._respond_with_error(403, 'access.denied')

        # TODO implement the etag check.
        base_obj = self._dao.select_one('id = :id_or_name OR name = :id_or_name',
                                        dict(id_or_name=id))
        if not base_obj:
            raise HTTPException(status_code=404, detail="Resource not found")

        base_obj_dict = base_obj.model_dump()
        updated_obj_dict = apply_changes(base_obj_dict, operations)
        updated_obj = self._dao.from_dict(updated_obj_dict)
        result = self._dao.simple_update(updated_obj,
                                         'id = :id_or_name OR name = :id_or_name',
                                         dict(id_or_name=id))

        return result if self._full_access_requested(request, access_claims) else self._hide_sensitive_fields(result)

    def delete(self,
               request: Request,
               id: str,
               access_claims: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]):
        """ Delete the resource by ID """
        if not self._check_authorization(DataAction.DELETE, access_claims=access_claims):
            return self._respond_with_error(403, 'access.denied')

        if self._dao.delete('id = :id_or_name OR name = :id_or_name', dict(id_or_name=id)) > 0:
            return make_generic_json_response(200)
        else:
            return make_generic_json_response(410)

    def _full_access_requested(self, request: Request, access_claims: Optional[Dict[str, Any]]) -> bool:
        given_scopes: List[str] = self._extract_scopes(access_claims)

        return request.headers.get('X-Access-Level') == "full" and len(self._privilege_scopes.intersection(given_scopes)) > 0

    def _hide_sensitive_fields(self, obj: T) -> T:
        return obj

    def _hide_sensitive_fields_in_list(self, objs: List[T]) -> List[T]:
        return [self._hide_sensitive_fields(obj) for obj in objs]
