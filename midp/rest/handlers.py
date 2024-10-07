from typing import TypeVar, Type, List

from fastapi import APIRouter
from imagination import container

from midp.common.base_rest_controller import BaseRestController
from midp.iam.models import IAMOAuthClient, IAMPolicy, IAMRole, IAMScope, IAMUser
from midp.rest.realm_rest_controller import PolicyRestController, ClientRestController, \
    RoleRestController, ScopeRestController, UserRestController

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

rest_routers = [
    create_router('clients', IAMOAuthClient, ClientRestController),
    create_router('policies', IAMPolicy, PolicyRestController),
    create_router('roles', IAMRole, RoleRestController),
    create_router('scopes', IAMScope, ScopeRestController),
    create_router('users', IAMUser, UserRestController),
]
