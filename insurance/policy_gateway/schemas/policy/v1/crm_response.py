import typing as t
import datetime as dt
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel

from insurance.domains.policy.dto import PolicyStatusEnum
from .common_structure import (
    PrevPolicy, ProductCode, InsuranceCode, LeadReference, Insurer, Period, ChannelCode, CreatorReference, Structure
)


class CRMPolicyResponse(BaseModel):
    reference: UUID
    created: dt.datetime
    status: str
    structure_reference: UUID
    product: ProductCode
    insurance: InsuranceCode
    lead: LeadReference
    premium: int
    coast: int
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


class PolicyListStructure(BaseModel):
    reference: UUID
    insurance: str
    insured: list[str]
    vehicles: list[str]
    phone: str
    iin: str
    global_id: t.Optional[str]
    creator: UUID
    amount: int
    reward: Decimal
    create_time: dt.datetime
    can_download: t.Optional[bool]
    insurer_title: str
    channel: str
    status: PolicyStatusEnum


class CRMPoliciesResponse(BaseModel):
    data: t.List[PolicyListStructure]
    items: int
    limit: int
    page: int
    pages_count: int
