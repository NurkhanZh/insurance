import attr
import datetime as dt
import typing as t
from decimal import Decimal
from types import MappingProxyType
from uuid import UUID
from pydantic import BaseModel, constr

from dateutil.relativedelta import relativedelta

from .enums import PolicyStatusEnum, PeriodTypeEnum, InsuranceNameEnum

LeadItemType = t.NewType('LeadItemType', t.Literal['driver', 'vehicle', 'limit'])
IIN = t.NewType('IIN', constr(pattern=r'\d{12}'))


@attr.s(auto_attribs=True, hash=True, frozen=True)
class StatusRecord:
    status: PolicyStatusEnum
    timestamp: attr.field(type=dt.datetime, order=dt.datetime)


@attr.s(frozen=True, auto_attribs=True)
class InsuranceInfo:
    insurance_reference: str
    redirect_url: str


class Period(BaseModel):
    type: PeriodTypeEnum
    value: int

    def end_date(self, begin_date: dt.date = None):
        begin_date = begin_date or dt.date.today()
        match self.type:
            case PeriodTypeEnum.YEAR:
                end_date = (begin_date + relativedelta(years=1))
                if end_date.day == begin_date.day:
                    end_date -= dt.timedelta(1)

        return end_date  # noqa


class StructureVehicle(BaseModel):
    registration_number: str


class StructureDriver(BaseModel):
    iin: str
    is_privileged: bool = False


class StructureLimit(BaseModel):
    value: int


class Structure(BaseModel):
    item_reference: t.Optional[UUID]
    title: str
    type: LeadItemType
    attrs: t.Union[StructureDriver, StructureVehicle, StructureLimit]


class PrevPolicy(BaseModel):
    prev_global_id: str
    insurance: InsuranceNameEnum


@attr.s(frozen=True, auto_attribs=True)
class InsuranceOffer:
    premium: int
    cost: int
    reward: Decimal
    attributes: MappingProxyType = attr.ib(converter=MappingProxyType)
    conditions: tuple[str] = attr.ib(converter=lambda x: tuple(x) if x else tuple())


@attr.s(frozen=True, auto_attribs=True)
class StatusInfo:
    status_type: PolicyStatusEnum
    timestamp: dt.datetime
    insurance_reference: t.Optional[str]
    global_id: t.Optional[str]
    extra_attrs: MappingProxyType = attr.ib(default=MappingProxyType(dict()),
                                            converter=lambda x: MappingProxyType(x if x else dict()))
