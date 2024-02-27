from enum import Enum

from insurance.integrations.policy.system_accounting.abstractions import SystemAccountingClientABC
from insurance.integrations.policy.system_accounting.base_client import BaseClient


class Path(str, Enum):
    CREATE_PAY_REWARD = '/v2/pay-qasco-reward/'
    CONFIRM_PAY_REWARD = '/v2/pay-qasco-reward/confirm/'
    CANCEL_REWARD = '/canceled-qasco-reward/'
    CREATE_RETENTION_REWARD = '/v2/retention-qasco-reward/'
    CONFIRM_RETENTION_REWARD = '/v2/retention-qasco-reward/confirm/'
    CANCEL_RETENTION_REWARD = '/canceled-retention-qasco-reward/'


class SystemAccountingClient(BaseClient, SystemAccountingClientABC):
    async def create_pay_reward(self, payload: dict) -> str:
        data = await self._request(method='POST', url=Path.CREATE_PAY_REWARD, json=payload)
        return data['document_reference']

    async def confirm_pay_reward(self, payload: dict):
        await self._request(method='POST', url=Path.CONFIRM_PAY_REWARD, json=payload)

    async def cancel_reward(self, payload: dict):
        await self._request(method='POST', url=Path.CANCEL_REWARD, json=payload)

    async def create_retention_reward(self, payload: dict) -> str:
        data = await self._request(method='POST', url=Path.CREATE_RETENTION_REWARD, json=payload)
        return data['document_reference']

    async def confirm_retention_reward(self, payload: dict):
        await self._request(method='POST', url=Path.CONFIRM_RETENTION_REWARD, json=payload)

    async def cancel_retention_reward(self, payload: dict):
        await self._request(method='POST', url=Path.CANCEL_RETENTION_REWARD, json=payload)
