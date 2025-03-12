from typing import List, Optional, Dict

from imagination.decorator.service import Service
from pydantic import BaseModel, Field

from midp.common.env_helpers import SELF_REFERENCE_URI
from midp.iam.dao.client import ClientDao
from midp.iam.dao.policy import PolicyDao
from midp.iam.dao.role import RoleDao
from midp.iam.dao.user import UserDao
from midp.iam.models import IAMPolicySubject, IAMPolicy, IAMOAuthClient, IAMRole, IAMUser
from midp.log_factory import get_logger_for_object


class InvalidSubjectError(RuntimeError):
    def __init__(self, subject: IAMPolicySubject):
        super().__init__(subject)

    @property
    def subject(self) -> IAMPolicySubject:
        return self.args[0]


class PolicyResolution(BaseModel):
    subjects: List[str] = Field(default_factory=list)
    policies: List[IAMPolicy] = Field(default_factory=list)


@Service()
class PolicyResolver(object):
    def __init__(self, client_dao: ClientDao, policy_dao: PolicyDao, role_dao: RoleDao, user_dao: UserDao):
        self._log = get_logger_for_object(self)
        self._self_reference_uri = SELF_REFERENCE_URI
        self._client_dao = client_dao
        self._policy_dao = policy_dao
        self._role_dao = role_dao
        self._user_dao = user_dao

    def evaluate(self,
                 /,
                 subjects: List[IAMPolicySubject],
                 resource_url: Optional[str] = None,
                 scopes: Optional[List[str]] = None) -> PolicyResolution:
        requested_scopes = set(scopes) if scopes else set()
        resource_url = resource_url or self._self_reference_uri

        actors: List[IAMOAuthClient | IAMRole | IAMUser] = list()

        for subject in subjects:
            subject_id = subject.subject
            subject_type = subject.kind

            if subject_type == 'client':
                client = self._client_dao.get(subject_id)
                if not client:
                    raise InvalidSubjectError(subject)
                actors.append(client)
            elif subject_type == 'role':
                role = self._role_dao.get(subject_id)
                if not role:
                    raise InvalidSubjectError(subject)
                actors.append(role)
            elif subject_type == 'user':
                user = self._user_dao.get(subject_id)
                if not user:
                    raise InvalidSubjectError(subject)
                actors.append(user)
                if user.roles:
                    # iterator = self._role_dao.select(where='name IN :names', parameters=dict(names=user.roles))  # FIXME There is a bug with binding the list parameter.
                    actors.extend(
                        role
                        for role in self._role_dao.select()
                        if role.name in user.roles
                    )
            else:
                raise NotImplementedError(subject_type)

        resolution = PolicyResolution(
            subjects=[f'{type(actor).__name__}/{actor.name}' for actor in actors],
        )

        policy_search_condition = "resource = :resource_url"
        resource_url_for_policy_search = resource_url
        if resource_url.endswith('/'):
            policy_search_condition = "resource LIKE :resource_url"
            resource_url_for_policy_search += r'%'

        policies_matched_by_subject: List[IAMPolicy] = []

        client_id_list = [client.name for client in actors if isinstance(client, IAMOAuthClient)]
        role_name_list = [role.name for role in actors if isinstance(role, IAMRole)]
        user_email_list = [user.email for user in actors if isinstance(user, IAMUser)]

        for policy in self._policy_dao.select(policy_search_condition,
                                              dict(resource_url=resource_url_for_policy_search)):
            for policy_subject in policy.subjects:
                if (
                        policy_subject.kind == 'client' and policy_subject.subject in client_id_list
                        or policy_subject.kind == 'role' and policy_subject.subject in role_name_list
                        or policy_subject.kind == 'user' and policy_subject.subject in user_email_list
                ):
                    policies_matched_by_subject.append(policy)

        # Now, use the scopes to fileter more.
        if requested_scopes:
            # Filter the policies with all scopes matched.
            requested_scopes_count = len(requested_scopes)

            resolution.policies.extend([
                policy
                for policy in policies_matched_by_subject
                if len(requested_scopes.intersection(policy.scopes)) == requested_scopes_count
            ])
        else:
            # Scope filter is NOT required.
            resolution.policies.extend(policies_matched_by_subject)

        return resolution
