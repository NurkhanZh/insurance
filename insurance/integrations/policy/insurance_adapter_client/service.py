import typing as t

from aiomisc import Service
from insurances_adapter.sdk.client import InsurancesSDK


class InsuranceAdapterBaseService(Service):
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__()
        self._client: InsurancesSDK = InsurancesSDK(base_url=base_url,
                                                    timeout=timeout)

    async def start(self):
        ...

    async def stop(self, exception: t.Optional[Exception] = None):
        session = self._client.get_session()
        if session:
            await session.aclose()

    @property
    def client(self):
        return self._client
