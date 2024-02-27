from fastapi import APIRouter

from insurance.policy_gateway.handlers.healthcheck import handler


class HealthCheckApiWithView:
    def __init__(self):
        self._router = APIRouter(prefix='')
        self._set_healthcheck_router()

    @property
    def router(self) -> APIRouter:
        return self._router

    def _set_healthcheck_router(self):
        router = APIRouter(prefix='/healthcheck', tags=['healthcheck'])
        router.get('')(handler.healthcheck_with_view)

        self._router.include_router(router)
