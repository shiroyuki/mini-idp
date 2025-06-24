import json
import os
import re
from typing import Optional, Any, Dict, List

import yaml
from imagination import container

from midp.common.env_helpers import required_env, optional_env
from midp.static_info import BOOTING_OPTIONS
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.scope import ScopeDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMUser, PredefinedRole, \
    PredefinedScope, PredefinedPolicy
from midp.log_factory import midp_logger
from midp.common.rds import DataStore, DataStoreSession
from midp.snapshot.models import AppSnapshot

log = midp_logger("snapshot.utils")


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

    session.commit()


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


class MissingSnapshotFileError(IOError):
    pass


class UnsupportedSnapshotFileFormatError(RuntimeError):
    pass


def _clear_operational_data(session: Optional[DataStoreSession] = None):
    if not session:
        datastore: DataStore = container.get(DataStore)
        session = datastore.session()

    log.debug("Resetting the data... [IN PROGRESS]")
    for reset_statement in [
        'DELETE FROM iam_scope WHERE id IS NOT NULL',
        'DELETE FROM iam_role WHERE id IS NOT NULL',
        'DELETE FROM iam_user WHERE id IS NOT NULL',
        'DELETE FROM iam_client WHERE id IS NOT NULL',
        'DELETE FROM iam_policy WHERE id IS NOT NULL',
    ]:
        session.execute_without_result(reset_statement)
    log.debug("Resetting the data... [COMPLETE]")


def _clear_session_data(session: Optional[DataStoreSession] = None):
    if not session:
        datastore: DataStore = container.get(DataStore)
        session = datastore.session()

    log.debug("Clearing the sessions... [IN PROGRESS]")
    for reset_statement in [
        'DELETE FROM kv WHERE k IS NOT NULL',
    ]:
        session.execute_without_result(reset_statement)
    log.debug("Clearing the sessions... [COMPLETE]")


def bootstrap(clear_operational_data: bool = False,
              clear_session_data: bool = False,
              snapshot_files: Optional[List[str]] = None,
              snapshots: Optional[List[AppSnapshot]] = None):
    BOOTSTRAP_SNAPSHOT = AppSnapshot(
        scopes=[scope.value for scope in PredefinedScope],
        roles=[role.value for role in PredefinedRole],
        users=[
            IAMUser(
                id=optional_env('MINI_IDP_BOOTSTRAP_OWNER_USER_ID', default=None),
                name=required_env('MINI_IDP_BOOTSTRAP_OWNER_USER_NAME'),
                email=required_env('MINI_IDP_BOOTSTRAP_OWNER_USER_EMAIL'),
                password=required_env('MINI_IDP_BOOTSTRAP_OWNER_USER_PASSWORD'),
                roles=[PredefinedRole.IDP_ROOT.value.name],
            ),
        ],
        clients=[],
        policies=[policy.value for policy in PredefinedPolicy],
    )

    datastore: DataStore = container.get(DataStore)
    session: DataStoreSession = datastore.session()

    if clear_operational_data:
        _clear_operational_data(session)

    if clear_session_data:
        _clear_session_data(session)

    # Restore from a snapshot.
    log.debug("Bootstrapping with the pre-defined resources... [IN PROGRESS]")
    restore_from_snapshot(BOOTSTRAP_SNAPSHOT, session=session)
    log.debug("Bootstrapping with the pre-defined resources... [COMPLETE]")

    # Restore from a file.
    if snapshot_files:
        loaded_snapshot_count: int = 0
        total_loaded_snapshot_count: int = len(snapshot_files)

        log.debug(f"Restoring with the snapshot files... [STARTING]")
        for snapshot_file in snapshot_files:
            actual_snapshot_file = os.path.abspath(snapshot_file)

            if os.path.exists(actual_snapshot_file):
                with open(actual_snapshot_file, 'r') as f:
                    snapshot_data: Dict[str, Any]
                    snapshot_data_raw = f.read()

                    if actual_snapshot_file.lower().endswith('.json'):
                        snapshot_data = json.loads(snapshot_data_raw)
                    elif re.search(r'\.ya?ml', actual_snapshot_file.lower()):
                        snapshot_data = yaml.load(snapshot_data_raw, Loader=yaml.SafeLoader)
                    else:
                        raise UnsupportedSnapshotFileFormatError(actual_snapshot_file)

                    snapshot = AppSnapshot(**snapshot_data)
                    try:
                        restore_from_snapshot(snapshot, session=session)
                        loaded_snapshot_count += 1
                        loading_progress = loaded_snapshot_count * 100.0 / total_loaded_snapshot_count
                        log.debug(f"Restoring with the snapshot files... [{'COMPLETE' if loading_progress == 100 else f'{loading_progress}%'}]")
                    except Exception as e:
                        log.error("Restoring with the snapshot files... [ERROR]")
                        session.roll_back()
                        raise RuntimeError(f'Failed to restore from a snapshot file {actual_snapshot_file}') from e
            else:
                log.error("Restoring with the snapshot files... [ERROR]")
                session.roll_back()
                raise MissingSnapshotFileError(actual_snapshot_file)

    if snapshots:
        loaded_snapshot_count: int = 0
        total_loaded_snapshot_count: int = len(snapshots)

        log.debug(f"Restoring with the snapshot objects... [STARTING]")
        for snapshot in snapshots:
            try:
                restore_from_snapshot(snapshot, session=session)
                loaded_snapshot_count += 1
                loading_progress = loaded_snapshot_count * 100.0 / total_loaded_snapshot_count
                log.debug(f"Restoring with the snapshot objects... [{'COMPLETE' if loading_progress == 100 else f'{loading_progress}%'}]")
            except Exception as e:
                log.error("Restoring with the snapshot objects... [ERROR]")
                session.roll_back()
                raise RuntimeError(f'Failed to restore from a snapshot object ({snapshot})') from e

    session.commit()
    session.close()


if BOOTING_OPTIONS:
    if 'bootstrap' not in BOOTING_OPTIONS:
        raise RuntimeError(f'The "bootstrap" option is not given.')

    raw_snapshot_files = optional_env('MINI_IDP_DEV_BOOTSTRAP_WITH_SNAPSHOTS', default='').strip()

    bootstrap(
        clear_operational_data='bootstrap:data-reset' in BOOTING_OPTIONS,
        clear_session_data='bootstrap:session-reset' in BOOTING_OPTIONS,
        snapshot_files=re.split(r'\s*,\s*', raw_snapshot_files) if raw_snapshot_files else [],
    )

__all__ = ["export_snapshot", "restore_from_snapshot"]
