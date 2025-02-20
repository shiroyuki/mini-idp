from typing import TypeVar, Generic, List, Optional, Union, Any, Dict, Annotated

from fastapi import HTTPException, Depends
from imagination import container
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from starlette.requests import Request
from starlette.responses import Response

from midp.common.enigma import Enigma
from midp.common.obj_patcher import SimpleJsonPatchOperation, apply_changes
from midp.common.token_manager import TokenParser, TokenManager
from midp.common.web_helpers import make_generic_json_response, retrieve_bearer_token, authenticate_with_bearer_token
from midp.iam.dao.atomic import AtomicDao

TypeParameter = TypeVar('TypeParameter')


class FailedResponse(BaseModel):
    error: str
    error_description: Optional[str] = None


class BaseRestController(Generic[TypeParameter]):
    _dao: AtomicDao[TypeParameter]

    def _respond_with_error(self, status: int, error: str, error_description: Optional[str] = None):
        return Response(
            status_code=status,
            content=FailedResponse(
                error=error,
                error_description=error_description
            ).model_dump_json(indent=2)
        )

    def _get_scopes_for_list(self) -> List[str]:
        raise NotImplementedError()

    def _get_scopes_for_get(self) -> List[str]:
        raise NotImplementedError()

    def _get_scopes_for_create(self) -> List[str]:
        raise NotImplementedError()

    def _get_scopes_for_update(self) -> List[str]:
        raise NotImplementedError()

    def _get_scopes_for_delete(self) -> List[str]:
        raise NotImplementedError()

    def _run_additional_checks(self):
        pass

    def list(self, request: Request, access_token: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> List[TypeParameter]:
        """ List resources """
        result = [i for i in self._dao.select()]
        return result if self._full_access_requested(request) else self._hide_sensitive_fields_in_list(result)

    def create(self, request: Request, obj: TypeParameter, access_token: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> TypeParameter:
        """ Create a new resource """
        result = self._dao.add(obj)
        return result if self._full_access_requested(request) else self._hide_sensitive_fields(result)

    def get(self, request: Request, id: str, access_token: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> Union[TypeParameter, FailedResponse]:
        """ Get the resource by ID """
        result = self._dao.select_one('id = :id_or_name OR name = :id_or_name',
                                      dict(id_or_name=id))
        if not result:
            return self._respond_with_error(status=404, error='not-found')
        else:
            return result if self._full_access_requested(request) else self._hide_sensitive_fields(result)

    def patch(self, request: Request, id: str, operations: List[SimpleJsonPatchOperation], access_token: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> Union[
        TypeParameter, FailedResponse]:
        # TODO implement the role and permission check.
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

        return result if self._full_access_requested(request) else self._hide_sensitive_fields(result)

    def put(self, request: Request, id: str, obj: TypeParameter, access_token: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]) -> Union[TypeParameter, FailedResponse]:
        result = self._dao.simple_update(obj,
                                         'id = :id_or_name OR name = :id_or_name',
                                         dict(id_or_name=id))

        return result if self._full_access_requested(request) else self._hide_sensitive_fields(result)

    def delete(self, request: Request, id: str, access_token: Annotated[Dict[str, Any], Depends(authenticate_with_bearer_token)]):
        """ Delete the resource by ID """
        if self._dao.delete('id = :id_or_name OR name = :id_or_name',
                            dict(id_or_name=id)) > 0:
            return make_generic_json_response(200)
        else:
            return make_generic_json_response(410)

    def _full_access_requested(self, request: Request) -> bool:
        return request.headers.get('X-Access-Level') == "full"

    def _hide_sensitive_fields(self, obj: TypeParameter) -> TypeParameter:
        return obj

    def _hide_sensitive_fields_in_list(self, objs: List[TypeParameter]) -> List[TypeParameter]:
        return [self._hide_sensitive_fields(obj) for obj in objs]
