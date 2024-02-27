import typing as t

from httpx import AsyncClient
from pydantic import BaseModel, ValidationError

from insurance.integrations.policy.qasco_backend.exceptions import ClientResponseError


class UserInfoModel(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    permissions: list[str]


class QascoBackendClient:
    _session: AsyncClient

    def set_session(self, session: AsyncClient):
        self._session = session

    async def get_user_info(self, token: str):
        headers = {'Authorization': token}
        response = await self._session.request(method='GET', url='/api/crm/v1/auth/user_info/', headers=headers)
        if response.status_code != 200:
            raise ClientResponseError()

    async def aclose(self):
        await self._session.aclose()
