from json import JSONDecodeError
from httpx import HTTPError, AsyncClient, Response
import typing as t
import insurance.integrations.policy.system_accounting.exceptions as exc


class BaseClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self._session = AsyncClient(base_url=base_url, timeout=timeout)

    async def aclose(self):
        await self._session.aclose()

    @t.final
    async def _request(self, method: str, url: str, json: dict = None, **kwargs) -> dict:
        response = await self._make_request(method, url, json, **kwargs)
        return self._parse_response_date(response)

    async def _make_request(self, method: str, url: str, json: dict = None, **kwargs) -> Response:
        try:
            return await self._session.request(method=method, url=url, json=json, **kwargs)
        except HTTPError:
            raise exc.UnknownAdapterError()

    @staticmethod
    def _parse_response_date(response: Response) -> dict:
        try:
            result = response.json()
        except JSONDecodeError:
            raise exc.DecodeJsonError(content_type=response.headers.get('content-type'), content=response.content)

        if not response.is_success or result.get('status') == 'ERROR':
            raise exc.ResponseAdapterError(result.get('message', 'Unknown error'))

        return result.get('data', {})
