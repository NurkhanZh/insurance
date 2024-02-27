import typing as t
from uuid import UUID

from httpx import AsyncClient

from .schemas import GetPersonResponse, GetDriversInfoResponse
from . import exceptions as exc


class PersonDomainSDK:

    def __init__(self, base_url: str, timeout: int = 10):
        self._base_url = base_url
        self._timeout = timeout

    async def get_client(self, iin: t.Optional[str], reference: t.Optional[UUID] = None) -> GetPersonResponse:
        param = dict()
        if iin:
            param['iin'] = iin
        if reference:
            param['reference'] = reference
        response = await self._send_request(
            method='GET',
            url='/internal/v2/client/person',
            params=param
        )
        return GetPersonResponse(**response[0])

    async def get_drivers_info(self, iin_list: t.Sequence[str]) -> GetDriversInfoResponse:
        param = {'iin': iin_list}
        response = await self._send_request(
            method='GET',
            url='/public/v2/client/get-drivers-info',
            params=param
        )
        return GetDriversInfoResponse.model_validate(response)

    async def _send_request(
            self,
            method: str,
            url: str,
            data: str | None = None,
            params: dict | None = None,
            headers: dict | None = None,
    ):
        async with AsyncClient(base_url=self._base_url, timeout=self._timeout) as _session:
            response = await _session.request(
                method=method,
                url=url,
                data=data,
                params=params,
                headers=headers,
            )
        data = response.json()
        self._check_error(status_code=response.status_code, data=data)
        return data['data']

    def _check_error(self, status_code: int, data: dict):
        if status_code != 200:
            raise exc.InternalServiceError(data)  # internal service with error
        if data['status'] == "ERROR":
            if data['exc_code'] == 'PersonNotFound':
                raise exc.PersonNotFound(data)  # PersonNotFound
            else:
                raise exc.InternalServiceError(data)  # Internal service
