from typing import TypeVar, Generic, List

from fastapi import HTTPException

from midp.common.web_helpers import make_generic_json_response
from midp.iam.dao.atomic import AtomicDao

TypeParameter = TypeVar('TypeParameter')


class BaseRestController(Generic[TypeParameter]):
    _dao: AtomicDao[TypeParameter]

    def list(self) -> List[TypeParameter]:
        """ List resources """
        return [i for i in self._dao.select()]

    def create(self, obj: TypeParameter) -> TypeParameter:
        """ Create a new resource """
        return self._dao.add(obj)

    def get(self, id: str) -> TypeParameter:
        """ Get the resource by ID """
        return self._dao.select('id = :id_or_name OR name = :id_or_name',
                                dict(id_or_name=id))

    def patch(self, id: str, obj: TypeParameter) -> TypeParameter:
        raise HTTPException(501)

    def put(self, id: str, obj: TypeParameter) -> TypeParameter:
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
