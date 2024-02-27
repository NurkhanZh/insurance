from uuid import UUID
import datetime as dt
from pydantic import BaseModel, Field, constr
import typing as t


IIN = t.NewType('IIN', constr(pattern=r'[\d]{12}'))


class DriverLicence(BaseModel):
    number: t.Optional[str]
    issue_date: t.Optional[dt.date]


class IdDocument(BaseModel):
    type: t.Optional[str] = Field(alias='document_type')
    number: t.Optional[str] = Field(alias='document_number')
    issue_date: t.Optional[dt.date] = Field(alias='document_date')


class GetPersonResponse(BaseModel):
    iin: str = Field(..., pattern=r'[\d]{12}', description='12 чисел')
    surname: t.Optional[str]
    name: t.Optional[str]
    reference: UUID
    id_document: t.Optional[IdDocument]
    driver_license: t.Optional[DriverLicence]
    required_id_document: bool
    can_drive_car: bool
    phone: t.Optional[str]
    required_phone_number: t.Optional[bool]
    is_privileged: t.Optional[bool] = False  # TODO: расширить ответ в клиенте полем is_privileged


class DriverInfo(BaseModel):
    iin: IIN
    reference: UUID
    is_valid_bmg_phone: t.Optional[bool]


class GetDriversInfoResponse(BaseModel):
    drivers: list[DriverInfo]
