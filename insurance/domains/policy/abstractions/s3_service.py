import abc
import typing as t
from uuid import UUID


class S3AdapterABC(abc.ABC):
    @abc.abstractmethod
    async def upload_policy_file(self, data: t.ByteString, policy_reference: UUID):
        """
        Метод для записи полиса в S3
        """

    @abc.abstractmethod
    def get_url(self, policy_reference: UUID) -> str:
        """
        Метод для получения ссылки на получение файла
        """
