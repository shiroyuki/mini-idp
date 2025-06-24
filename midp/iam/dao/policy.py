from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import IAMPolicy
from midp.common.rds import DataStore


@Service()
class PolicyDao(AtomicDao[IAMPolicy]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMPolicy, IAMPolicy.__tbl__)

        self.map_column_as_json('subjects')\
            .map_column_as_json('scopes')
