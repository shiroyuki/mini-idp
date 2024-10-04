from typing import TypeVar, Type, List

from fastapi import APIRouter
from imagination import container

from midp.iam.models import Realm
from midp.rest.data_service import BaseRestController, RealmRestController, UserRestController, ScopeRestController, \
    RoleRestController, PolicyRestController, ClientRestController

T = TypeVar('T')


def create_router(resource_type: str, model_class: Type[T], controller_class: Type[BaseRestController[T]]) -> APIRouter:
    router = APIRouter(
        prefix=f'/rest/{resource_type}',
        tags=[f'rest:{resource_type}'],
        responses={
            401: dict(error='not-authenticated'),
            403: dict(error='access-denied'),
            404: dict(error='not-found'),
            405: dict(error='method-not-allowed'),
            410: dict(error='gone'),
        }
    )

    controller: BaseRestController[T] = container.get(controller_class)

    router.get('/', response_model=List[model_class])(controller.list)
    router.post('/')(controller.create)
    router.get('/{id}', response_model=model_class)(controller.get)
    router.patch('/{id}')(controller.patch)
    router.put('/{id}')(controller.put)
    router.delete('/{id}')(controller.delete)

    return router

rest_client_router = create_router('clients', Realm, ClientRestController)
rest_policy_router = create_router('policies', Realm, PolicyRestController)
rest_realm_router = create_router('realms', Realm, RealmRestController)
rest_role_router = create_router('roles', Realm, RoleRestController)
rest_scope_router = create_router('scopes', Realm, ScopeRestController)
rest_user_router = create_router('users', Realm, UserRestController)


# rest_realm_router = APIRouter(
#     prefix=r'/rest/realms',
#     tags=['rest:realms'],
#     responses={
#         401: dict(error='not-authenticated'),
#         403: dict(error='access-denied'),
#         404: dict(error='job-not-found'),
#         405: dict(error='method-not-allowed'),
#         410: dict(error='gone'),
#     }
# )
#
# controller = RestController(Realm, container.get(RealmDao))
#
# rest_realm_router.get('/')(controller.list)
# rest_realm_router.post('/')(controller.create)
# rest_realm_router.get('/{id_or_name}')(controller.get)
# rest_realm_router.delete('/{id_or_name}')(controller.delete)
