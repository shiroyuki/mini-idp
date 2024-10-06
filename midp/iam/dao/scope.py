from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import IAMScope
from midp.rds import DataStore


@Service()
class ScopeDao(AtomicDao[IAMScope]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMScope, IAMScope.__tbl__)
        self.column('id')\
            .column('realm_id')\
            .column('name')\
            .column('description')\
            .column('sensitive')

    def get(self, realm_id: str, id: str) -> IAMScope:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id)', dict(realm_id=realm_id, id=id))
