from typing import TypeVar, Generic, List

from fastapi import HTTPException
from imagination.decorator.service import Service

from midp.common.web_helpers import make_generic_json_response
from midp.iam.dao.atomic import AtomicDao
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.realm import RealmDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import Realm, IAMPolicy, OAuthClient, IAMRole, IAMScope, IAMUser

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
                                dict(id_or_name=id)
                                )

    def patch(self, id: str, obj: TypeParameter) -> TypeParameter:
        raise HTTPException(405)

    def put(self, id: str, obj: TypeParameter) -> TypeParameter:
        raise HTTPException(405)

    def delete(self, id: str):
        """ Delete the resource by ID """
        if self._dao.delete('id = :id_or_name OR name = :id_or_name',
                            dict(id_or_name=id)) > 0:
            return make_generic_json_response(200)
        else:
            return make_generic_json_response(410)


@Service()
class RealmRestController(BaseRestController[Realm]):
    def __init__(self, dao: RealmDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[Realm]:
        return super().list()

    def create(self, obj: Realm) -> Realm:
        return super().create(obj)

    def get(self, id: str) -> Realm:
        return super().get(id)

    def patch(self, id: str, obj: Realm) -> Realm:
        return super().patch(id, obj)

    def put(self, id: str, obj: Realm) -> Realm:
        return super().put(id, obj)

    def delete(self, id: str):
        return super().delete(id)


@Service()
class PolicyRestController(BaseRestController[IAMPolicy]):
    def __init__(self, dao: PolicyDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[IAMPolicy]:
        return super().list()

    def create(self, obj: IAMPolicy) -> IAMPolicy:
        return super().create(obj)

    def get(self, id: str) -> IAMPolicy:
        return super().get(id)

    def patch(self, id: str, obj: IAMPolicy) -> IAMPolicy:
        return super().patch(id, obj)

    def put(self, id: str, obj: IAMPolicy) -> IAMPolicy:
        return super().put(id, obj)

    def delete(self, id: str):
        return super().delete(id)


@Service()
class ClientRestController(BaseRestController[OAuthClient]):
    def __init__(self, dao: ClientDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[OAuthClient]:
        return super().list()

    def create(self, obj: OAuthClient) -> OAuthClient:
        return super().create(obj)

    def get(self, id: str) -> OAuthClient:
        return super().get(id)

    def patch(self, id: str, obj: OAuthClient) -> OAuthClient:
        return super().patch(id, obj)

    def put(self, id: str, obj: OAuthClient) -> OAuthClient:
        return super().put(id, obj)

    def delete(self, id: str):
        return super().delete(id)


@Service()
class RoleRestController(BaseRestController[IAMRole]):
    def __init__(self, dao: RoleDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[IAMRole]:
        return super().list()

    def create(self, obj: IAMRole) -> IAMRole:
        return super().create(obj)

    def get(self, id: str) -> IAMRole:
        return super().get(id)

    def patch(self, id: str, obj: IAMRole) -> IAMRole:
        return super().patch(id, obj)

    def put(self, id: str, obj: IAMRole) -> IAMRole:
        return super().put(id, obj)

    def delete(self, id: str):
        return super().delete(id)


@Service()
class ScopeRestController(BaseRestController[IAMScope]):
    def __init__(self, dao: ScopeDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[IAMScope]:
        return super().list()

    def create(self, obj: IAMScope) -> IAMScope:
        return super().create(obj)

    def get(self, id: str) -> IAMScope:
        return super().get(id)

    def patch(self, id: str, obj: IAMScope) -> IAMScope:
        return super().patch(id, obj)

    def put(self, id: str, obj: IAMScope) -> IAMScope:
        return super().put(id, obj)

    def delete(self, id: str):
        return super().delete(id)


@Service()
class UserRestController(BaseRestController[IAMUser]):
    def __init__(self, dao: UserDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[IAMUser]:
        return super().list()

    def create(self, obj: IAMUser) -> IAMUser:
        return super().create(obj)

    def get(self, id: str) -> IAMUser:
        return super().get(id)

    def patch(self, id: str, obj: IAMUser) -> IAMUser:
        return super().patch(id, obj)

    def put(self, id: str, obj: IAMUser) -> IAMUser:
        return super().put(id, obj)

    def delete(self, id: str):
        return super().delete(id)
