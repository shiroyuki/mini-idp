from typing import TypeVar, Generic, List, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from starlette.responses import Response

from midp.common.obj_patcher import SimpleJsonPatchOperation, apply_changes
from midp.common.web_helpers import make_generic_json_response
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

    def list(self) -> List[TypeParameter]:
        """ List resources """
        return [i for i in self._dao.select()]

    def create(self, obj: TypeParameter) -> TypeParameter:
        """ Create a new resource """
        return self._dao.add(obj)

    def get(self, id: str) -> Union[TypeParameter, FailedResponse]:
        """ Get the resource by ID """
        result = self._dao.select_one('id = :id_or_name OR name = :id_or_name',
                                 dict(id_or_name=id))
        if not result:
            return self._respond_with_error(status=404, error='not-found')
        else:
            return result

    def patch(self, id: str, operations: List[SimpleJsonPatchOperation]) -> Union[TypeParameter, FailedResponse]:
        # TODO implement the role and permission check.
        # TODO implement the etag check.
        base_obj = self._dao.select_one('id = :id_or_name OR name = :id_or_name',
                                        dict(id_or_name=id))
        if not base_obj:
            raise HTTPException(status_code=404, detail="Resource not found")

        base_obj_dict = base_obj.model_dump()
        updated_obj_dict = apply_changes(base_obj_dict, operations)
        updated_obj = self._dao.from_dict(updated_obj_dict)
        return self._dao.simple_update(updated_obj,
                                       'id = :id_or_name OR name = :id_or_name',
                                       dict(id_or_name=id))

    def put(self, id: str, obj: TypeParameter) -> Union[TypeParameter, FailedResponse]:
        return self._dao.simple_update(obj,
                                       'id = :id_or_name OR name = :id_or_name',
                                       dict(id_or_name=id))

    def delete(self, id: str):
        """ Delete the resource by ID """
        if self._dao.delete('id = :id_or_name OR name = :id_or_name',
                            dict(id_or_name=id)) > 0:
            return make_generic_json_response(200)
        else:
            return make_generic_json_response(410)
