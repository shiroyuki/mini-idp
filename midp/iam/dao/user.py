from typing import Any, Dict, List

from imagination.decorator.service import Service

from midp.common.enigma import Enigma
from midp.iam.dao.atomic import AtomicDao, InsertError
from midp.iam.dao.role import RoleDao
from midp.iam.models import IAMUser, IAMRole
from midp.rds import DataStore


@Service()
class UserDao(AtomicDao[IAMUser]):
    def __init__(self, datastore: DataStore, role_dao: RoleDao, enigma: Enigma):
        super().__init__(datastore, IAMUser, IAMUser.__tbl__)
        self._role_dao = role_dao

        self._enigma = enigma

        self.column('id') \
            .column('realm_id') \
            .column('name') \
            .column('password', 'encrypted_password',
                    convert_to_sql_data=lambda v: self._enigma.encrypt(v).decode(),
                    convert_to_property_data=lambda v: self._enigma.decrypt(v).decode()) \
            .column('email') \
            .column('full_name')

    def get(self, realm_id: str, id: str) -> IAMUser:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id OR email = :id)',
                               dict(realm_id=realm_id, id=id))

    def map_row(self, row: Dict[str, Any]) -> IAMUser:
        user: IAMUser = super().map_row(row)
        user.roles.extend(self._get_roles_for(user.id))
        return user

    # @override # for Python 3.12
    def add(self, obj: IAMUser) -> IAMUser:
        user: IAMUser = super().add(obj)

        if user.roles:
            parameter_set: List[Dict[str, Any]] = []

            roles = self._role_dao.select(
                'realm_id = :realm_id AND (id IN :id_list OR name IN (:id_list))',
                dict(realm_id=user.realm_id, id_list=user.roles)
            )

            for role in roles:
                parameter_set.append(dict(user_id=user.id, role_id=role.id))

            additional_insertions = """
                INSERT INTO iam_user_role (user_id, role_id)
                VALUES (:user_id, :role_id)
            """

            if self._datastore.execute_without_result(additional_insertions, parameter_set) == 0:
                raise InsertError(user)

        return user

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
