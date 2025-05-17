from typing import Optional

from imagination.decorator.service import Service
from pydantic import BaseModel

from midp.common.token_manager import TokenManager
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMUserReadOnly, IAMPolicySubject
from midp.log_factory import midp_logger, midp_logger_for


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
    def __init__(self, user_dao: UserDao, token_manager: TokenManager):
        self._log = midp_logger_for(self)
        self._user_dao = user_dao
        self._token_manager = token_manager

    def authenticate(self, username: str, password: str, resource_url: Optional[str] = None) -> AuthenticationResult:
        user = self._user_dao.get(username)

        from midp.common.enigma import Enigma
        from imagination.standalone import use
        enigma = use(Enigma)

        self._log.warning(f"PANDA: user={user.name}: user.password='{user.password}' (hash={enigma.compute_hash(user.password)})")
        self._log.warning(f"PANDA: user={user.name}: password='{password}' (hash={enigma.compute_hash(password)})")
        self._log.warning(f"PANDA: user={user.name}: password == user.password --> {password == user.password}")

        if user and user.password == password:
            policy_subject = IAMPolicySubject(subject=user.name, kind="user")
            token_set = self._token_manager.create_token_set(subject=policy_subject, resource_url=resource_url)

            return AuthenticationResult(
                principle=IAMUserReadOnly.build_from(user),
                access_token=token_set.access_token,
                refresh_token=token_set.refresh_token,
            )
        else:
            self._log.warning("Invalid username/password combination")
            raise AuthenticationError('invalid_credential', 'Invalid Credential')
