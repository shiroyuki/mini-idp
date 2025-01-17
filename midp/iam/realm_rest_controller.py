from typing import List, Union

from imagination.decorator.service import Service

from midp.common.obj_patcher import SimpleJsonPatchOperation
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicy, IAMOAuthClient, IAMRole, IAMScope, IAMUser
from midp.common.base_rest_controller import BaseRestController, FailedResponse


@Service()
class PolicyRestController(BaseRestController[IAMPolicy]):
    def __init__(self, dao: PolicyDao):
        self._dao = dao

    # The repeat here is just for FastAPI's method reflection.

    def list(self) -> List[IAMPolicy]:
        return super().list()

    def create(self, obj: IAMPolicy) -> IAMPolicy:
        return super().create(obj)

    def get(self, id: str) -> Union[IAMPolicy, FailedResponse]:
        return super().get(id)

    def patch(self, id: str, operations: List[SimpleJsonPatchOperation]) -> Union[IAMPolicy, FailedResponse]:
        return super().patch(id, operations)

    def put(self, id: str, obj: IAMPolicy) -> Union[IAMPolicy, FailedResponse]:
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

    def get(self, id: str) -> Union[IAMOAuthClient, FailedResponse]:
        return super().get(id)

    def patch(self, id: str, operations: List[SimpleJsonPatchOperation]) -> Union[IAMOAuthClient, FailedResponse]:
        return super().patch(id, operations)

    def put(self, id: str, obj: IAMOAuthClient) -> Union[IAMOAuthClient, FailedResponse]:
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

    def get(self, id: str) -> Union[IAMRole, FailedResponse]:
        return super().get(id)

    def patch(self, id: str, operations: List[SimpleJsonPatchOperation]) -> Union[IAMRole, FailedResponse]:
        return super().patch(id, operations)

    def put(self, id: str, obj: IAMRole) -> Union[IAMRole, FailedResponse]:
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

    def get(self, id: str) -> Union[IAMScope, FailedResponse]:
        return super().get(id)

    def patch(self, id: str, operations: List[SimpleJsonPatchOperation]) -> Union[IAMScope, FailedResponse]:
        return super().patch(id, operations)

    def put(self, id: str, obj: IAMScope) -> Union[IAMScope, FailedResponse]:
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

    def get(self, id: str) -> Union[IAMUser, FailedResponse]:
        return super().get(id)

    def patch(self, id: str, operations: List[SimpleJsonPatchOperation]) -> Union[IAMUser, FailedResponse]:
        return super().patch(id, operations)

    def put(self, id: str, obj: IAMUser) -> Union[IAMUser, FailedResponse]:
        return super().put(id, obj)

    def delete(self, id: str):
        return super().delete(id)
