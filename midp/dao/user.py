from typing import Any, Dict, List

from imagination.decorator.service import Service

from midp.dao.atomic import AtomicDao
from midp.dao.role import RoleDao
from midp.models import IAMUser, IAMRole
from midp.rds import DataStore


@Service()
class UserDao(AtomicDao[IAMUser]):
    def __init__(self, datastore: DataStore, role_dao: RoleDao):
        super().__init__(datastore, IAMUser.__tbl__)
        self._role_dao = role_dao

    def map_row(self, row: Dict[str, Any]) -> IAMUser:
        user = IAMUser(
            id=row['id'],
            realm_id=row['realm_id'],
            name=row['name'],
            password=None,
            email=row['email'],
            full_name=row['full_name'],
            roles=self._get_roles_for(row['id']),
        )
        return user

    # @override # for Python 3.12
    def add(self, obj: IAMUser) -> IAMUser:
        query = f"""
                INSERT INTO {self._table_name} (id, realm_id, name, hashed_password, password_salt, email, full_name)
                VALUES (:id, :realm_id, :name, :hashed_password, :password_salt, :email, :full_name)
                """.strip()

        parameters = {
            "id": obj.id,
            "realm_id": obj.realm_id,
            "name": obj.name,
            "hashed_password": obj.password,  # TODO Hash this password
            "password_salt": '',  # TODO Generate the partial salt
            "email": obj.email,
            "full_name": obj.full_name,
        }

        self._datastore.execute_without_result(query, parameters)

        if obj.roles:
            parameter_set: List[Dict[str, Any]] = []

            roles = self._role_dao.select(
                'realm_id = :realm_id AND (id IN :id_list OR name IN (:id_list))',
                dict(realm_id=obj.realm_id, id_list=obj.roles)
            )

            for role in roles:
                parameter_set.append(dict(user_id=obj.id, role_id=role.id))

            self._datastore.execute_without_result(
                """
                INSERT INTO iam_user_role (user_id, role_id)
                VALUES (:user_id, :role_id)
                """,
                parameters=parameter_set
            )

        return obj

    def _get_roles_for(self, user_id: str) -> List[str]:
        query = f"""
            SELECT role.name
            FROM {IAMRole.__tbl__} role
            INNER JOIN iam_user_role user_role
                ON (role.id = user_role.role_id)
            WHERE user_role.user_id = :user_id
        """
        return [
            role.name
            for role in self._datastore.execute(query, dict(user_id=user_id))
        ]
