from typing import List

from imagination.standalone import container
from pydantic import BaseModel, Field

from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMScope, IAMRole, IAMUser, IAMOAuthClient, IAMPolicy
from midp.log_factory import get_logger_for


class MainConfig(BaseModel):
    version: str = Field(default='1.0.0')
    scopes: List[IAMScope] = Field(default_factory=list)  # Auxiliary Property: Augmented
    roles: List[IAMRole] = Field(default_factory=list)  # Auxiliary Property: Augmented
    users: List[IAMUser] = Field(default_factory=list)  # Auxiliary Property: Augmented
    clients: List[IAMOAuthClient] = Field(default_factory=list)  # Auxiliary Property: Augmented
    policies: List[IAMPolicy] = Field(default_factory=list)  # Auxiliary Property: Augmented


def restore_from_snapshot(main_config: MainConfig):
    scope_dao: ScopeDao = container.get(ScopeDao)
    role_dao: RoleDao = container.get(RoleDao)
    user_dao: UserDao = container.get(UserDao)
    client_dao: ClientDao = container.get(ClientDao)
    policy_dao: PolicyDao = container.get(PolicyDao)

    for scope in main_config.scopes:
        scope_dao.add(scope)

    for role in main_config.roles:
        role_dao.add(role)

    for user in main_config.users:
        user_dao.add(user)

    for client in main_config.clients:
        client_dao.add(client)

    for policy in main_config.policies:
        policy_dao.add(policy)


def export_snapshot() -> MainConfig:
    scope_dao: ScopeDao = container.get(ScopeDao)
    role_dao: RoleDao = container.get(RoleDao)
    user_dao: UserDao = container.get(UserDao)
    client_dao: ClientDao = container.get(ClientDao)
    policy_dao: PolicyDao = container.get(PolicyDao)

    return MainConfig(
        scopes=[i for i in scope_dao.select()],
        roles=[i for i in role_dao.select()],
        users=[i for i in user_dao.select()],
        clients=[i for i in client_dao.select()],
        policies=[i for i in policy_dao.select()],
    )
