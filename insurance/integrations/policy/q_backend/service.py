import typing as t
from typing import Any

from aiomisc import Service
from httpx import AsyncClient

from .client import QascoBackendClient


class QascoBackendService(Service):
    def __init__(self, base_url: str, timeout=30, **kwargs: t.Any):
        super().__init__(**kwargs)
        self._client = QascoBackendClient()
        self._client.set_session(AsyncClient(base_url=base_url, timeout=timeout))

    @property
    def client(self):
        return self._client

    async def start(self) -> Any:
        ...

    async def stop(self, exception: t.Optional[Exception] = None):
        await self._client.aclose()

