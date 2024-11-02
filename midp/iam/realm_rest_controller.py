from typing import List

from imagination.decorator.service import Service

from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicy, IAMOAuthClient, IAMRole, IAMScope, IAMUser
from midp.common.base_rest_controller import BaseRestController


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
class ClientRestController(BaseRestController[IAMOAuthClient]):
    def __init__(self, dao: ClientDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[IAMOAuthClient]:
        return super().list()

    def create(self, obj: IAMOAuthClient) -> IAMOAuthClient:
        return super().create(obj)

    def get(self, id: str) -> IAMOAuthClient:
        return super().get(id)

    def patch(self, id: str, obj: IAMOAuthClient) -> IAMOAuthClient:
        return super().patch(id, obj)

    def put(self, id: str, obj: IAMOAuthClient) -> IAMOAuthClient:
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
