from imagination.decorator.service import Service

from midp.common.base_rest_controller import BaseRestController
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicy, IAMOAuthClient, IAMRole, IAMScope, IAMUser


@Service()
class PolicyRestController(BaseRestController[IAMPolicy]):
    def __init__(self, dao: PolicyDao):
        self._dao = dao


@Service()
class ClientRestController(BaseRestController[IAMOAuthClient]):
    def __init__(self, dao: ClientDao):
        self._dao = dao


@Service()
class RoleRestController(BaseRestController[IAMRole]):
    def __init__(self, dao: RoleDao):
        self._dao = dao


@Service()
class ScopeRestController(BaseRestController[IAMScope]):
    def __init__(self, dao: ScopeDao):
        self._dao = dao


@Service()
class UserRestController(BaseRestController[IAMUser]):
    def __init__(self, dao: UserDao):
        self._dao = dao

    def _hide_sensitive_fields(self, obj: IAMUser) -> IAMUser:
        return obj.model_copy(update={"password": None}, deep=False)
