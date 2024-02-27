from insurance.domains.policy.abstractions.adapters import QascoBackendAdapterABC
from insurance.integrations.policy.qasco_backend import QascoBackendClient


class QascoBackendAdapter(QascoBackendAdapterABC):
    def __init__(self, client: QascoBackendClient):
        self._client = client

    async def check_token(self, token: str):
        await self._client.get_user_info(token)
