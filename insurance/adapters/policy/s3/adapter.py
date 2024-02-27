import typing as t
import datetime as dt
from uuid import UUID
from wsgiref import handlers

from insurance.domains.policy.abstractions import S3AdapterABC
from insurance.infrastructure.s3.client import S3Client

YEAR_AND_DAY: t.Final[int] = 367


class S3Adapter(S3AdapterABC):
    """
    S3Client(
        session=ClientSession(),
        url=self._config.path,
        secret_access_key=self._config.secret_key,
        access_key_id=self._config.access_key,
    )
    """

    def __init__(self, client: S3Client, file_url_pattern: str):
        self._client = client
        self._file_url_pattern = file_url_pattern

    async def upload_policy_file(self, data: t.ByteString, policy_reference: UUID):
        year_from_now = dt.datetime.today() + dt.timedelta(days=YEAR_AND_DAY)
        await self._client.put(
            f'policies/{policy_reference}.pdf',
            data=bytes(data),
            headers={
                'x-amz-acl': 'public-read',
                'Content-Type': 'application/pdf',
                'Expires': handlers.format_date_time(year_from_now.timestamp())
            }
        )
        if not await self.check_policy_file(policy_reference):
            raise FileNotFoundError(f'Not found policy in s3 by reference: {policy_reference}')

    async def check_policy_file(self, policy_reference: UUID) -> bool:
        response = await self._client.request(
            'HEAD',
            f'policies/{policy_reference}.pdf',
            headers={
                'x-amz-acl': 'public-read',
                'Content-Type': 'application/pdf',
            }
        )
        if response.status_code == 200:
            return True
        return False

    def get_url(self, policy_reference: UUID) -> str:
        return f'{self._file_url_pattern}{policy_reference}.pdf'
