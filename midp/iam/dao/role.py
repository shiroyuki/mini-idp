from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import IAMRole
from midp.rds import DataStore


@Service()
class RoleDao(AtomicDao[IAMRole]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMRole, IAMRole.__tbl__)
        self.column('id')\
            .column('realm_id')\
            .column('name')\
            .column('description')

    def get(self, realm_id: str, id: str) -> IAMRole:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id)', dict(realm_id=realm_id, id=id))
