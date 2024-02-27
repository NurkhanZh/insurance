import typing as t
from uuid import UUID

from pydantic import BaseModel, field_validator

from insurance.domains.policy.dto import PeriodTypeEnum, ProductTypeEnum, InsuranceNameEnum

ItemType: t.TypeAlias = t.Literal['driver', 'vehicle', 'limit']


class ConditionCode(BaseModel):
    code: str


class Insurer(BaseModel):
    is_privileged: bool = False
    reference: UUID
    title: str


class Period(BaseModel):
    type: PeriodTypeEnum
    value: int


class ProductCode(BaseModel):
    code: ProductTypeEnum


class VehicleAttrsDetail(BaseModel):
    registration_number: str


class LimitAttrsDetail(BaseModel):
    value: int


class DriverAttrsDetail(BaseModel):
    iin: str
    is_privileged: bool = True


class Structure(BaseModel):
    item_reference: t.Optional[UUID]
    title: str
    type: ItemType
    attrs: t.Union[DriverAttrsDetail, VehicleAttrsDetail, LimitAttrsDetail]


class LeadReference(BaseModel):
    reference: UUID


class InsuranceCode(BaseModel):
    code: InsuranceNameEnum

    @field_validator('code', mode='before')
    def to_lower(cls, value: str):
        if value:
            value = value.lower()

        return value


class PrevPolicy(BaseModel):
    global_id: str
    description: str
    insurance: InsuranceCode


class ChannelCode(BaseModel):
    code: str


class CreatorReference(BaseModel):
    reference: UUID