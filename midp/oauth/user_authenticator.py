from time import sleep
from typing import Optional

from imagination.decorator.service import Service
from pydantic import BaseModel

from midp.iam.dao.user import UserDao
from midp.iam.models import IAMUserReadOnly


class AuthenticationResult(BaseModel):
    principle: IAMUserReadOnly
    access_token: str
    refresh_token: str


class AuthenticationError(RuntimeError):
    def __init__(self, code: str, description: str):
        super().__init__(code, description)

    @property
    def code(self):
        return self.args[0]

    @property
    def description(self):
        return self.args[1]


@Service()
class UserAuthenticator:
    def __init__(self, user_dao: UserDao):
        self._user_dao = user_dao

    def authenticate(self, username: str, password: str) -> AuthenticationResult:
        user = self._user_dao.get(username)

        if user and user.password == password:
            return AuthenticationResult(
                principle=IAMUserReadOnly.build_from(user),
                access_token='',
                refresh_token='',
            )
        else:
            raise AuthenticationError('invalid_credential', 'Invalid Credential')
