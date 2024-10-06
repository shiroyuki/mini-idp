from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao
from midp.models import Realm
from midp.rds import DataStore


@Service()
class RealmDao(AtomicDao[Realm]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, Realm, Realm.__tbl__)

        self.column('id')\
            .column('name')

    def get(self, id: str) -> Realm:
        return self.select_one('(id = :id OR name = :id)', dict(id=id))
