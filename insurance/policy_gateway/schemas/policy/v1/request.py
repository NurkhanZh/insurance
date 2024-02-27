import typing as t
import datetime as dt
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel
from insurance.domains.policy.dto import InsuranceNameEnum


class Lead(BaseModel):
    reference: UUID


class InsuranceCode(BaseModel):
    code: InsuranceNameEnum


class CreatePolicyRequest(BaseModel):
    lead: Lead
    insurance: InsuranceCode


class UpdatePolicyRequest(BaseModel):
    address: t.Optional[str] = None
    begin_date: t.Optional[dt.date] = None
    email: t.Optional[str] = None


class EurasiaRetentionAttrs(BaseModel):
    refund_amount: Decimal


class SetRescindedPolicyRequest(BaseModel):
    global_id: str
    timestamp: dt.datetime
    attributes: t.Optional[EurasiaRetentionAttrs] = None


class EurasiaReissuedPolicyAttributes(BaseModel):
    with_inexperienced: bool
    region_changed: bool


class SetReissuedPolicyRequest(BaseModel):
    global_id: str
    timestamp: dt.datetime
    attributes: t.Optional[EurasiaReissuedPolicyAttributes] = None


class SetOperatorErrorRequest(BaseModel):
    global_id: str
    timestamp: dt.datetime

