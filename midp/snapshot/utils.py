from typing import Optional

from imagination import container

from midp.common.env_helpers import SELF_REFERENCE_URI, BOOTING_OPTIONS, required_env
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMScope, IAMUser, IAMPolicy, IAMPolicySubject, IDP_OWNER, IDP_ADMIN, IDP_USER
from midp.rds import DataStore, DataStoreSession
from midp.snapshot.models import AppSnapshot


def restore_from_snapshot(main_config: AppSnapshot, session: Optional[DataStoreSession] = None):
    if not session:
        datastore: DataStore = container.get(DataStore)
        session = datastore.session()

    scope_dao: ScopeDao = container.get(ScopeDao)
    role_dao: RoleDao = container.get(RoleDao)
    user_dao: UserDao = container.get(UserDao)
    client_dao: ClientDao = container.get(ClientDao)
    policy_dao: PolicyDao = container.get(PolicyDao)

    for scope in main_config.scopes:
        scope_dao.add(scope, datastore_session=session)

    for role in main_config.roles:
        role_dao.add(role, datastore_session=session)

    for user in main_config.users:
        user_dao.add(user, datastore_session=session)

    for client in main_config.clients:
        client_dao.add(client, datastore_session=session)

    for policy in main_config.policies:
        policy_dao.add(policy, datastore_session=session)


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


if BOOTING_OPTIONS:
    if 'bootstrap' not in BOOTING_OPTIONS:
        raise RuntimeError(f'The "bootstrap" option is not given.')

    COMMON_SCOPES = [
        # OpenID scopes
        IAMScope(name='openid'),
        IAMScope(name='profile'),
        # App-specific Scopes
        IAMScope(name='idp.client.read'),
        IAMScope(name='idp.policy.read'),
        IAMScope(name='idp.role.read'),
        IAMScope(name='idp.scope.read'),
        IAMScope(name='idp.user.read'),
        IAMScope(name='idp.user.write'),
    ]

    ADMIN_SCOPES = [
        IAMScope(name='idp.admin'),
        IAMScope(name='idp.client.read_sensitive'),
        IAMScope(name='idp.client.write'),
        IAMScope(name='idp.policy.write'),
        IAMScope(name='idp.role.write'),
        IAMScope(name='idp.scope.write'),
    ]

    BOOTSTRAP_SNAPSHOT = AppSnapshot(
        scopes=COMMON_SCOPES + ADMIN_SCOPES,
        roles=[
            IDP_OWNER,
            IDP_ADMIN,
            IDP_USER,
        ],
        users=[
            IAMUser(
                name=required_env('MINI_IDP_BOOTSTRAP_OWNER_USER_NAME'),
                email=required_env('MINI_IDP_BOOTSTRAP_OWNER_USER_EMAIL'),
                password=required_env('MINI_IDP_BOOTSTRAP_OWNER_USER_PASSWORD'),
                roles=[IDP_OWNER.name],
            ),
        ],
        clients=[],
        policies=[
            IAMPolicy(
                name='idp.admins',
                resource=SELF_REFERENCE_URI,
                subjects=[
                    IAMPolicySubject(kind='role', subject=IDP_OWNER.name),
                    IAMPolicySubject(kind='role', subject=IDP_ADMIN.name),
                ],
                scopes=[s.name for s in COMMON_SCOPES + ADMIN_SCOPES],
            ),
            IAMPolicy(
                name='idp.users',
                resource=SELF_REFERENCE_URI,
                subjects=[IAMPolicySubject(kind='role', subject=IDP_USER.name)],
                scopes=[s.name for s in COMMON_SCOPES],
            ),
        ],
    )

    datastore: DataStore = container.get(DataStore)
    session: DataStoreSession = datastore.session()

    if 'bootstrap:reset' in BOOTING_OPTIONS:
        for reset_statement in [
            'DELETE FROM iam_scope WHERE id IS NOT NULL',
            'DELETE FROM iam_role WHERE id IS NOT NULL',
            'DELETE FROM iam_user WHERE id IS NOT NULL',
            'DELETE FROM iam_client WHERE id IS NOT NULL',
            'DELETE FROM iam_policy WHERE id IS NOT NULL',
            'DELETE FROM kv WHERE k IS NOT NULL',
        ]:
            session.execute_without_result(reset_statement)

    restore_from_snapshot(BOOTSTRAP_SNAPSHOT, session=session)
    session.commit()
    session.close()

__all__ = ["export_snapshot", "restore_from_snapshot"]
