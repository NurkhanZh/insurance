from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class BaseSystemAccountingSchema(BaseModel):
    ...


class PolicyPayRewardCreateRequestSchema(BaseSystemAccountingSchema):
    reference: UUID
    amount: Decimal
    channel_id: str
    insurance_id: str


class PolicyPayRewardConfirmRequestSchema(BaseSystemAccountingSchema):
    reference: UUID
    insurance_id: str


class PolicyRetentionRewardCreateRequestSchema(BaseSystemAccountingSchema):
    reference: UUID
    amount: Decimal
    channel_id: str
    insurance_id: str


class PolicyRetentionRewardConfirmRequestSchema(BaseSystemAccountingSchema):
    reference: UUID
    insurance_id: str


class PolicyCanceledRewardSchema(BaseSystemAccountingSchema):
    reference: UUID
    insurance_id: str


class PolicyCanceledRetentionRewardSchema(BaseSystemAccountingSchema):
    reference: UUID
    insurance_id: str
