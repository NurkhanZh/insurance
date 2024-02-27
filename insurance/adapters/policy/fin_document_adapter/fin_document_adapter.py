from uuid import UUID

from insurance.adapters.policy.fin_document_adapter.converter import Converter
from insurance.domains.policy.abstractions import FinDocumentAdapterABC
from insurance.domains.policy.dto import InsuranceNameEnum
from insurance.domains.policy.model import Policy
from insurance.integrations.policy.system_accounting import SystemAccountingClientABC


class FinDocumentAdapter(FinDocumentAdapterABC):
    def __init__(self, client: SystemAccountingClientABC):
        self._client = client

    async def create_pay_reward(self, policy: Policy) -> UUID:
        payload = Converter.get_create_pay_reward_payload(policy)
        document_reference = await self._client.create_pay_reward(payload)
        return UUID(document_reference)

    async def confirm_pay_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        payload = Converter.get_confirm_pay_reward_payload(policy_reference, insurance)
        await self._client.confirm_pay_reward(payload)

    async def cancel_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        payload = Converter.get_canceled_reward_payload(policy_reference, insurance)
        await self._client.cancel_reward(payload)

    async def create_retention_reward(self, policy: Policy) -> UUID:
        payload = Converter.get_create_retention_reward_payload(policy)
        document_reference = await self._client.create_retention_reward(payload)
        return UUID(document_reference)

    async def confirm_retention_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        payload = Converter.get_confirm_retention_reward_payload(policy_reference, insurance)
        await self._client.confirm_retention_reward(payload)

    async def cancel_retention_reward(self, policy_reference: UUID, insurance: InsuranceNameEnum):
        payload = Converter.get_canceled_retention_reward_payload(policy_reference, insurance)
        await self._client.cancel_retention_reward(payload)
