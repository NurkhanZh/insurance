import typing as t
from uuid import UUID

from pydantic import BaseModel


class RequiredPhone(BaseModel):
    required: bool
    allow_bmg: bool
    allow_otp: bool


class RequiredInsurerData(BaseModel):
    phone: RequiredPhone


class RequiredDriverData(BaseModel):
    reference: UUID
    phone: RequiredPhone


class RequiredPolicyData(BaseModel):
    drivers: t.Sequence[RequiredDriverData] = []
    insurer: t.Optional[RequiredInsurerData] = None
