import typing as t
from mimetypes import guess_type

from httpx import AsyncClient

from insurance.infrastructure.s3.signer import AwsRequestSigner

CONTENT_TYPE: t.Final[str] = "Content-Type"


class S3Client:
    def __init__(self,
                 session: AsyncClient,
                 url: str,
                 secret_access_key: str,
                 access_key_id: str,
                 ):
        self._session = session
        self._url = url
        self._signer = AwsRequestSigner(
            region="", service="s3", access_key_id=access_key_id,
            secret_access_key=secret_access_key,
        )

    async def put(self, object_name: str, data: bytes, headers: t.Optional[dict] = None, **kwargs):
        return await self.request('PUT', object_name, data=data, headers=headers, **kwargs)

    async def request(
            self,
            method: str,
            path: str,
            headers: t.Optional[dict] = None,
            data: t.Optional[bytes] = None,
            **kwargs,
    ):
        url = f'{self._url}/{path.lstrip("/")}'
        headers = self._make_headers(headers, file_path=path)
        headers.update(
            self._signer.sign_with_headers(
                method, url, headers=headers, content_hash="UNSIGNED-PAYLOAD",
            ),
        )
        return await self._session.request(
            method, url, headers=headers, data=data, **kwargs,
        )

    @staticmethod
    def _make_headers(
            headers: t.Optional[dict] = None,
            file_path: str = "",
    ):
        headers = dict(headers or {})
        if CONTENT_TYPE not in headers:
            content_type = guess_type(file_path)[0]
            if content_type is None:
                content_type = "application/octet-stream"

            headers[CONTENT_TYPE] = content_type
        return headers
