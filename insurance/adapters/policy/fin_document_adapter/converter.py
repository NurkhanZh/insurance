from uuid import UUID

from insurance.adapters.policy.fin_document_adapter.schemas import (
    PolicyPayRewardCreateRequestSchema,
    PolicyPayRewardConfirmRequestSchema,
    PolicyRetentionRewardCreateRequestSchema,
    PolicyRetentionRewardConfirmRequestSchema,
    PolicyCanceledRewardSchema,
    PolicyCanceledRetentionRewardSchema,
)
from insurance.domains.policy.dto import InsuranceNameEnum
from insurance.domains.policy.model import Policy


class Converter:
    @staticmethod
    def get_create_pay_reward_payload(policy: Policy) -> dict:
        policy_state = policy.state
        schema = PolicyPayRewardCreateRequestSchema(
            reference=policy_state.reference,
            amount=policy_state.reward,
            channel_id=policy_state.channel,
            insurance_id=policy_state.insurance.value.upper(),
        )
        return schema.model_dump(mode='json')

    @staticmethod
    def get_confirm_pay_reward_payload(reference: UUID, insurance: InsuranceNameEnum) -> dict:
        schema = PolicyPayRewardConfirmRequestSchema(reference=reference, insurance_id=insurance.value.upper())
        return schema.model_dump(mode='json')

    @staticmethod
    def get_create_retention_reward_payload(policy: Policy) -> dict:
        policy_state = policy.state
        schema = PolicyRetentionRewardCreateRequestSchema(
            reference=policy_state.reference,
            amount=policy_state.reward,
            channel_id=policy_state.channel,
            insurance_id=policy_state.insurance.value.upper(),
        )
        return schema.model_dump(mode='json')

    @staticmethod
    def get_confirm_retention_reward_payload(reference: UUID, insurance: InsuranceNameEnum) -> dict:
        schema = PolicyRetentionRewardConfirmRequestSchema(reference=reference, insurance_id=insurance.value.upper())
        return schema.model_dump(mode='json')

    @staticmethod
    def get_canceled_reward_payload(reference: UUID, insurance: InsuranceNameEnum) -> dict:
        result = PolicyCanceledRewardSchema(reference=reference, insurance_id=insurance.value.upper())
        return result.model_dump(mode='json')

    @staticmethod
    def get_canceled_retention_reward_payload(reference: UUID, insurance: InsuranceNameEnum) -> dict:
        result = PolicyCanceledRetentionRewardSchema(reference=reference, insurance_id=insurance.value.upper())
        return result.model_dump(mode='json')
