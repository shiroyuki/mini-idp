from time import time
from typing import Dict, Any, Optional, Tuple, Union
from uuid import uuid4

from imagination.decorator.service import Service

from midp.common.enigma import Enigma
from midp.common.key_storage import KeyStorage
from midp.static_info import access_token_ttl


class Session:
    def __init__(self, manager, id: str, encrypted_id: str, data: Dict[str, Any], expires: Union[int, float]):
        self.__manager = manager
        self.__id = id
        self.__encrypted_id = encrypted_id
        self.__data = data
        self.__expires = expires

    @property
    def id(self):
        return self.__id

    @property
    def encrypted_id(self):
        return self.__encrypted_id

    @property
    def data(self):
        return self.__data

    @property
    def expires(self):
        return self.__expires

    @property
    def is_unset(self):
        return not bool(self.__data)

    def save(self):
        self.__manager.save(self)

    def __repr__(self):
        return f'<Session id={self.__id} data={self.__data}>'


@Service()
class SessionManager:
    def __init__(self, enigma: Enigma, kv: KeyStorage):
        self._enigma = enigma
        self._kv = kv

    def get_metadata(self, id: Optional[str] = None, encrypted_id: Optional[str] = None) -> Tuple[str, int]:
        if id:
            session_id = id
        elif encrypted_id:
            session_id = self._enigma.decrypt(encrypted_id).decode()
        else:
            session_id = str(uuid4())

        return session_id, time() + access_token_ttl

    def load(self, id: Optional[str] = None, encrypted_id: Optional[str] = None) -> Session:
        session_id, expiry_timestamp = self.get_metadata(id, encrypted_id)

        return Session(manager=self,
                       id=session_id,
                       encrypted_id=self._enigma.encrypt(session_id).decode(),
                       data=self._kv.get(f'session:{session_id}') or dict(),
                       expires=expiry_timestamp)

    def save(self, session: Session):
        self._kv.set(f'session:{session.id}', session.data, time() + access_token_ttl)
