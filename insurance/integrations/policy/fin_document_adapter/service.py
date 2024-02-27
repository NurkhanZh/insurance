import typing as t

from aiomisc import Service

from insurance.integrations.policy.system_accounting import SystemAccountingClientABC, SystemAccountingClient


class FinDocumentService(Service):
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__()
        self._client: SystemAccountingClientABC = SystemAccountingClient(base_url=base_url, timeout=timeout)

    async def start(self):
        ...

    async def stop(self, exception: t.Optional[Exception] = None):
        await self._client.aclose()

    @property
    def client(self):
        return self._client
