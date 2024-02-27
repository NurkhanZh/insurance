import typing as t
import datetime as dt
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel

from .common_structure import (
    PrevPolicy, ProductCode, InsuranceCode, LeadReference, Insurer, Period, ChannelCode, CreatorReference, Structure
)


class InternalPolicyResponse(BaseModel):
    reference: UUID
    created: dt.datetime
    status: str
    structure_reference: UUID
    product: ProductCode
    insurance: InsuranceCode
    lead: LeadReference
    premium: int
    coast: int
    reward: Decimal
    retention_reward: t.Optional[Decimal]
    prev_policy: t.Optional[PrevPolicy]
    insurer: Insurer
    phone: str
    structure: t.List[t.Dict]
    attributes: t.Dict
    period: Period
    begin_date: dt.date
    end_date: dt.date
    global_id: t.Optional[str]
    address: t.Optional[str]
    conditions: t.Optional[t.List[str]]
    email: t.Optional[str]
    redirect_url: t.Optional[str]
    downloaded: t.Optional[bool]
    channel: ChannelCode
    creator: CreatorReference
    policy_history: t.Optional[t.List[dict]]


class InternalPolicyListStructure(BaseModel):
    reference: UUID
    begin_date: dt.date
    coast: int
    reward: Decimal
    structure_reference: UUID
    conditions: t.Optional[t.List[str]]
    insurance: InsuranceCode
    insurer: Insurer
    period: Period
    phone: str
    premium: int
    prev_policy: t.Optional[PrevPolicy]
    product: ProductCode
    status: str
    structure: t.List[Structure]
    created: dt.datetime
    downloaded: t.Optional[bool]


class InternalPoliciesResponse(BaseModel):
    data: t.List[InternalPolicyListStructure]
    items: int
    limit: int
    page: int
    pages_count: int
