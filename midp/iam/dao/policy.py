from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import IAMPolicy
from midp.rds import DataStore


@Service()
class PolicyDao(AtomicDao[IAMPolicy]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMPolicy, IAMPolicy.__tbl__)

        self.column('id')\
            .column('realm_id')\
            .column('name')\
            .column_as_json('subjects')\
            .column('resource')\
            .column_as_json('scopes')

    def get(self, realm_id: str, id: str) -> IAMPolicy:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id)', dict(realm_id=realm_id, id=id))
