from fastapi import Request, HTTPException
from starlette import status

from insurance.domains.policy.abstractions.adapters import QascoBackendAdapterABC


class CrmAuth:
    def __init__(self, adapter: QascoBackendAdapterABC):
        self._adapter = adapter

    async def __call__(self, request: Request):
        if token := request.headers.get('Authorization'):
            request.scope['user'] = await self._adapter.check_token(token)
            return
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
