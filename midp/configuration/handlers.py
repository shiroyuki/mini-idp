from imagination import container

from midp.configuration.models import AppSnapshot
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao


def restore_from_snapshot(main_config: AppSnapshot):
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


def export_snapshot() -> AppSnapshot:
    scope_dao: ScopeDao = container.get(ScopeDao)
    role_dao: RoleDao = container.get(RoleDao)
    user_dao: UserDao = container.get(UserDao)
    client_dao: ClientDao = container.get(ClientDao)
    policy_dao: PolicyDao = container.get(PolicyDao)

    return AppSnapshot(
        scopes=[i for i in scope_dao.select()],
        roles=[i for i in role_dao.select()],
        users=[i for i in user_dao.select()],
        clients=[i for i in client_dao.select()],
        policies=[i for i in policy_dao.select()],
    )
