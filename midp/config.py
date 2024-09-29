from typing import Dict, List
from imagination.standalone import container
from pydantic import BaseModel, Field
import yaml

from midp.dao.realm import RealmDao
from midp.dao.role import RoleDao
from midp.dao.scope import ScopeDao
from midp.dao.user import UserDao
from midp.models import Realm


class MainConfig(BaseModel):
    version: str = Field(default='1.0.0')
    realms: List[Realm]


def restore_from_files(config_file_paths: List[str]):
    """ Load from multiple files """
    main_config = MainConfig(realms=[])
    realms: Dict[str, Realm] = dict()

    for config_file_path in config_file_paths:
        config = restore_from_one_file(config_file_path)
        for realm in config.realms:
            realms[realm.name] = realm

    main_config.realms.extend(realms.values())

    restore_from_main_config(main_config=main_config)


def restore_from_one_file(config_file_path: str):
    """ Load from one file """
    with open(config_file_path, 'r') as f:
        raw_config = yaml.load(f.read(), Loader=yaml.BaseLoader)
        return MainConfig(**raw_config)


def restore_from_main_config(main_config: MainConfig):
    realm_dao: RealmDao = container.get(RealmDao)
    scope_dao: ScopeDao = container.get(ScopeDao)
    role_dao: RoleDao = container.get(RoleDao)
    user_dao: UserDao = container.get(UserDao)

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

        for policy in realm.policies:
            policy.realm_id = realm.id
