from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import IAMRole
from midp.common.rds import DataStore


@Service()
class RoleDao(AtomicDao[IAMRole]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMRole, IAMRole.__tbl__)
