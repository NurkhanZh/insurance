import typing as t
from uuid import UUID

from httpx import AsyncClient

from . import exceptions as exc
from .schemas import GetVehicleResponse


class VehicleDomainSDK:

    def __init__(self, base_url: str, timeout: int = 10):
        self._base_url = base_url
        self._timeout = timeout

    async def get_vehicle(
            self,
            registration_number: t.Optional[str],
            reference: t.Optional[UUID] = None,
    ) -> GetVehicleResponse:
        params = dict()
        if reference:
            params['reference'] = reference
        if registration_number:
            params['registration_number'] = registration_number
        response = await self._send_request(
            method='GET',
            url='/internal/v4/vehicle',
            params=params
        )
        return GetVehicleResponse(**response)

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
            raise exc.InternalServiceError(data)
        if data['status'] == "ERROR":
            if data['exc_code'] == 'CachedVehicleNotFound':
                raise exc.VehicleNotFound(data)
            else:
                raise exc.InternalServiceError(data)
