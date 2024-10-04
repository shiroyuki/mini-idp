from typing import List, Optional

from imagination.standalone import container
from pydantic import BaseModel, Field

from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.realm import RealmDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.log_factory import get_logger_for
from midp.iam.models import Realm


class MainConfig(BaseModel):
    version: str = Field(default='1.0.0')
    realms: List[Realm]


def restore_from_snapshot(main_config: MainConfig):
    logger = get_logger_for('snapshot_loader')

    realm_dao: RealmDao = container.get(RealmDao)
    scope_dao: ScopeDao = container.get(ScopeDao)
    role_dao: RoleDao = container.get(RoleDao)
    user_dao: UserDao = container.get(UserDao)
    client_dao: ClientDao = container.get(ClientDao)
    policy_dao: PolicyDao = container.get(PolicyDao)

    for realm in main_config.realms:
        realm_dao.add(realm)

        for scope in realm.scopes:
            scope.realm_id = realm.id
            scope_dao.add(scope)

        for role in realm.roles:
            role.realm_id = realm.id
            role_dao.add(role)

        for user in realm.users:
            user.realm_id = realm.id
            user_dao.add(user)

        for client in realm.clients:
            client.realm_id = realm.id
            client_dao.add(client)

        for policy in realm.policies:
            policy.realm_id = realm.id
            policy_dao.add(policy)


def export_snapshot(realm_ids: Optional[List[str]] = None) -> MainConfig:
    realm_dao: RealmDao = container.get(RealmDao)
    scope_dao: ScopeDao = container.get(ScopeDao)
    role_dao: RoleDao = container.get(RoleDao)
    user_dao: UserDao = container.get(UserDao)
    client_dao: ClientDao = container.get(ClientDao)
    policy_dao: PolicyDao = container.get(PolicyDao)

    main_config = MainConfig(realms=[])

    realms = (
        realm_dao.select('id IN :ids OR name IN :ids', dict(ids=realm_ids))
        if realm_ids
        else realm_dao.select()
    )

    for realm in realms:
        main_config.realms.append(
            Realm(
                id=realm.id,
                name=realm.name,
                scopes=[i for i in scope_dao.select('realm_id = :realm_id', dict(realm_id=realm.id))],
                roles=[i for i in role_dao.select('realm_id = :realm_id', dict(realm_id=realm.id))],
                users=[i for i in user_dao.select('realm_id = :realm_id', dict(realm_id=realm.id))],
                clients=[i for i in client_dao.select('realm_id = :realm_id', dict(realm_id=realm.id))],
                policies=[i for i in policy_dao.select('realm_id = :realm_id', dict(realm_id=realm.id))],
            )
        )

    return main_config
