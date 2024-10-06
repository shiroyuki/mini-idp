from imagination.decorator.service import Service

from midp.rds import DataStore


@Service()
class RootUserDao:
    def __init__(self, datastore: DataStore):
        self._datastore = datastore