import typing as t

from aiomisc import Service
from httpx import AsyncClient

from .client import S3Client


class S3Service(Service):
    def __init__(self, timeout, url: str, secret_access_key: str, access_key_id: str,):
        super().__init__()
        self._session: AsyncClient = AsyncClient(timeout=timeout)
        self._client: S3Client = S3Client(session=self._session,
                                          url=url,
                                          secret_access_key=secret_access_key,
                                          access_key_id=access_key_id)

    async def start(self):
        pass

    async def stop(self, exception: t.Optional[Exception] = None):
        await self._session.aclose()

    @property
    def client(self):
        return self._client
