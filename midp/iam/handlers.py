from typing import TypeVar, Type, List

from fastapi import APIRouter
from imagination import container
from imagination.standalone import use

from midp.common.base_rest_controller import BaseRestController
from midp.iam.models import IAMOAuthClient, IAMPolicy, IAMRole, IAMScope, IAMUser
from midp.iam.realm_rest_controller import PolicyRestController, ClientRestController, \
    RoleRestController, ScopeRestController, UserRestController
from midp.rds import DataStore

T = TypeVar('T')

common_router = APIRouter(
    prefix=f'/rest/iam',
    tags=[f'rest:iam'],
    responses={
        401: dict(error='not-authenticated'),
        403: dict(error='access-denied'),
        404: dict(error='not-found'),
        405: dict(error='method-not-allowed'),
        410: dict(error='gone'),
    }
)


@common_router.get('/stats')
def get_iam_resource_statistics():
    ...
    db = use(DataStore)
    return [
        {
            k: getattr(row, k)
            for k in row._fields
        }
        for row in db.execute(""" SELECT (SELECT COUNT(id) FROM iam_client) AS iam_client_count,
                                         (SELECT COUNT(id) FROM iam_policy) AS iam_policy_count,
                                         (SELECT COUNT(id) FROM iam_role)   AS iam_role_count,
                                         (SELECT COUNT(id) FROM iam_scope)  AS iam_scope_count,
                                         (SELECT COUNT(id) FROM iam_user)   AS iam_user_count,
                                         NOW()                              AS updated_at
                              """)
    ][0]


def create_router(resource_type: str, model_class: Type[T], controller_class: Type[BaseRestController[T]]) -> APIRouter:
    router = APIRouter(
        prefix=f'/rest/iam/{resource_type}',
        tags=[f'rest:iam:{resource_type}'],
        responses={
            401: dict(error='not-authenticated'),
            403: dict(error='access-denied'),
            404: dict(error='not-found'),
            405: dict(error='method-not-allowed'),
            410: dict(error='gone'),
        }
    )

    controller: BaseRestController[T] = container.get(controller_class)

    router.get(
        '/',
        summary=f'{resource_type.upper()}: List resources',
        response_model=List[model_class],
    )(controller.list)

    router.post(
        '/',
        summary=f'{resource_type.upper()}: Create a new resource',
        response_model=model_class,
    )(controller.create)

    router.get(
        '/{id}',
        summary=f'{resource_type.upper()}: Get a resource by ID',
        response_model=model_class,
    )(controller.get)

    router.put(
        '/{id}',
        summary=f'{resource_type.upper()}: Patch a resource identified by ID',
        response_model=model_class,
    )(controller.patch)

    router.delete(
        '/{id}',
        summary=f'{resource_type.upper()}: Delete a resource by ID',
    )(controller.delete)

    return router


iam_rest_routers = [
    common_router,
    create_router('clients', IAMOAuthClient, ClientRestController),
    create_router('policies', IAMPolicy, PolicyRestController),
    create_router('roles', IAMRole, RoleRestController),
    create_router('scopes', IAMScope, ScopeRestController),
    create_router('users', IAMUser, UserRestController),
]
