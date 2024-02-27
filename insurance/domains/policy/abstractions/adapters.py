import abc
import typing as t
import datetime as dt
from uuid import UUID

from insurance.domains.policy.dto import Lead, InsuranceOffer, InsuranceNameEnum, InsuranceInfo, StatusInfo
from insurance.domains.policy.model import Policy


class LeadAdapterABC(abc.ABC):
    @abc.abstractmethod
    async def get_lead(self, lead_reference: UUID) -> Lead:
        """
        Получения лида по reference лида
        """

    @abc.abstractmethod
    async def get_offer(self, insurance: InsuranceNameEnum, lead_reference: UUID) -> InsuranceOffer:
        """
        Получения оффера по лиду
        """


class OfferAdapterABC(abc.ABC):
    @abc.abstractmethod
    async def get_offer(self, policy: Policy) -> InsuranceOffer:
        """
        Получения оффера по полису
        """


class InsuranceAdapterABC(abc.ABC):

    @abc.abstractmethod
    async def save_policy(self, policy: Policy) -> InsuranceInfo:
        """
        Метод сохранение полиса в СК
        """
    @abc.abstractmethod
    async def get_policy_pdf(self, insurance_reference: str, insurance: InsuranceNameEnum) -> bytes:
        """
        Метод для получения pdf файл полиса в виде байтов от СК
        """


class CallbackAdapterABC(abc.ABC):

    @abc.abstractmethod
    def get_status_info(self,
                        insurance_reference: str,
                        global_id: t.Optional[str],
                        event_type: str,
                        event_time: dt.datetime,
                        attributes_json: str) -> StatusInfo:
        """
        Метод для получения StatusInfo по переданным параметрам
        """


class FinDocumentAdapterABC(abc.ABC):

    @abc.abstractmethod
    async def create_pay_reward(self, policy: Policy) -> UUID:
        """
        Метод для создания начисления вознаграждения
        """

    @abc.abstractmethod
    async def confirm_pay_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        """
        Метод для подтверждения начисления вознаграждения
        """

    @abc.abstractmethod
    async def cancel_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        """
        Метод для отмены вознаграждения
        """

    @abc.abstractmethod
    async def create_retention_reward(self, policy: Policy) -> UUID:
        """
        Метод для создания удержанного вознаграждения
        """

    @abc.abstractmethod
    async def confirm_retention_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        """
        Метод для подтверждения удержанного вознаграждения
        """

    @abc.abstractmethod
    async def cancel_retention_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        """
        Метод для отмены удержанного вознаграждения
        """


class QascoBackendAdapterABC(abc.ABC):

    @abc.abstractmethod
    async def check_token(self, token: str):
        """
        token type: Token token
        Метод для проверки токена
        """
