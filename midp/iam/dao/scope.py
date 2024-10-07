from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import IAMScope
from midp.rds import DataStore


@Service()
class ScopeDao(AtomicDao[IAMScope]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMScope, IAMScope.__tbl__)
