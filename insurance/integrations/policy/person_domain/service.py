import typing as t

from .sdk import PersonDomainSDK
from aiomisc import Service


class ClientDomainService(Service):

    def __init__(self, base_url: str, timeout, **kwargs: t.Any):
        super().__init__(**kwargs)
        self._client = PersonDomainSDK(base_url=base_url, timeout=timeout)

    @property
    def client(self):
        return self._client

    async def start(self) -> t.Any:
        ...

    async def stop(self, exception: Exception = None) -> t.Any:
        ...
