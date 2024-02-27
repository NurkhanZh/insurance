import typing as t

from aiomisc import Service
from insurance.sdk_clients.offer_sdk import OfferGatewayClient


class OfferService(Service):
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__()
        self._client: OfferGatewayClient = OfferGatewayClient(base_url=base_url, timeout=timeout)

    async def start(self):
        ...

    async def stop(self, exception: t.Optional[Exception] = None):
        ...

    @property
    def client(self):
        return self._client
