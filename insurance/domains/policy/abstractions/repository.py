import abc
from uuid import UUID

from insurance.domains.policy.model import Policy


class PolicyRepositoryABC(abc.ABC):

    @abc.abstractmethod
    async def get(self, reference: UUID) -> Policy:
        """
        Метод для получения полиса из БД
        """

    @abc.abstractmethod
    async def get_reference_by_insurance_reference(self, insurance_reference: str) -> UUID:
        """
        Метод для получения референса полса по insurance_reference
        """
