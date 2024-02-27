import typing as t

from fastapi import APIRouter, Depends

from insurance.domains.policy.abstractions.adapters import QascoBackendAdapterABC
from insurance.domains.policy import exceptions as exc
from insurance.policy_gateway.api.policy.dependencies import CrmAuth
from insurance.policy_gateway.handlers.policy.v4 import internal_handler, public_handler, crm_handler


class PolicyApiV4:
    def __init__(self, qasco_backend_adapter: QascoBackendAdapterABC = None):
        self._router = APIRouter()
        self._set_internal_policy_router()
        self._set_public_policy_router()
        self._set_crm_policy_router(qasco_backend_adapter)

    @property
    def router(self) -> APIRouter:
        return self._router

    def _set_internal_policy_router(self):
        router = APIRouter(tags=['internal'], prefix='/internal/v4/policy')
        router.post('')(internal_handler.create_policy)
        router.get('')(internal_handler.get_policies)
        router.get('/{reference}')(internal_handler.get_policy)
        self._router.include_router(router)

    def _set_public_policy_router(self):
        router = APIRouter(tags=['public'], prefix='/public/v4/policy')
        router.get('')(public_handler.get_policies)
        router.get('/{reference}')(public_handler.get_policy)
        router.patch('/{reference}')(public_handler.update_policy)
        router.post('/{reference}/save')(public_handler.save_to_insurance)
        router.get('/{reference}/pdf')(public_handler.get_policy_pdf)
        router.get('/{reference}/get-required-data')(public_handler.get_required_data)
        self._router.include_router(router)

    def _set_crm_policy_router(self, qasco_backend_adapter):
        router = APIRouter(tags=['crm'],
                           dependencies=[Depends(CrmAuth(qasco_backend_adapter))],
                           prefix='/crm/v4/policy')
        router.get('')(crm_handler.get_policies)
        router.get('/{reference}')(crm_handler.get_policy)
        router.post('/{reference}/set-rescinded')(crm_handler.set_rescinded_policy)
        router.post('/{reference}/set-operator-error')(crm_handler.set_operator_error_policy)
        router.post('/{reference}/set-reissued')(crm_handler.set_reissued_policy)
        self._router.include_router(router)


class PolicyApiV1:
    def __init__(self, qasco_backend_adapter: QascoBackendAdapterABC = None):
        self._router = APIRouter()
        self._set_internal_policy_router()
        self._set_public_policy_router()
        self._set_crm_policy_router(qasco_backend_adapter)

    @property
    def router(self) -> APIRouter:
        return self._router

    def _set_internal_policy_router(self):
        router = APIRouter(tags=['internal'], prefix='/internal/v/policy')
        router.post('', description='Создание Полиса',
                    responses={
                        400: {'model': t.Union[
                            exc.LeadGetOfferError.model(),
                            exc.LeadNotFoundError.model(),
                            exc.LeadMustBeFreeze.model()
                        ]}
                    }
                    )(internal_handler.create_policy)
        router.get('', description='Получение списка Полисов')(internal_handler.get_policies)
        router.get('/{reference}', description='Получение Полиса',
                   responses={
                       404: {'model': exc.PolicyNotFoundError.model()},
                   }
                   )(internal_handler.get_policy)
        self._router.include_router(router)

    def _set_public_policy_router(self):
        router = APIRouter(tags=['public'], prefix='/public/v/policy')
        router.get('')(public_handler.get_policies)
        router.get('/{reference}', description='Получение Полиса',
                   responses={
                       404: {'model': exc.PolicyNotFoundError.model()},
                   }
                   )(public_handler.get_policy)
        router.patch('/{reference}', description='Обновление Полиса',
                     responses={
                         404: {'model': exc.PolicyNotFoundError.model()},
                     }
                     )(public_handler.update_policy)
        router.post('/{reference}/save', description='Сохранение Полиса на стороне СК',
                    responses={
                        404: {'model': exc.PolicyNotFoundError.model()},
                    }
                    )(public_handler.save_to_insurance)
        router.get('/{reference}/pdf', description='Получение ПДФ файла Полиса',
                   responses={
                       404: {'model': exc.PolicyNotFoundError.model()},
                   }
                   )(public_handler.get_policy_pdf)
        router.get('/{reference}/get-required-data', description='Получение доп данных для оформления Полиса',
                   responses={
                       404: {'model': exc.PolicyNotFoundError.model()}
                   })(public_handler.get_required_data)
        self._router.include_router(router)

    def _set_crm_policy_router(self, qasco_backend_adapter):
        router = APIRouter(tags=['crm'],
                           dependencies=[Depends(CrmAuth(qasco_backend_adapter))],
                           prefix='/crm/v/policy')
        router.get('')(crm_handler.get_policies)
        router.get('/{reference}', description='Получение Полиса',
                   responses={
                       404: {'model': exc.PolicyNotFoundError.model()},
                   })(crm_handler.get_policy)
        router.post('/{reference}/set-rescinded',
                    description='Обновить статус Полиса на Расторгнут',
                    responses={
                        404: {'model': exc.PolicyNotFoundError.model()},
                    })(crm_handler.set_rescinded_policy)
        router.post('/{reference}/set-operator-error',
                    description='Обновить статус Полиса на Ошибку оператора',
                    responses={
                        404: {'model': exc.PolicyNotFoundError.model()},
                    })(crm_handler.set_operator_error_policy)
        router.post('/{reference}/set-reissued',
                    description='Обновить статус Полиса на Переоформлен',
                    responses={
                        404: {'model': exc.PolicyNotFoundError.model()},
                    }
                    )(crm_handler.set_reissued_policy)
        self._router.include_router(router)
