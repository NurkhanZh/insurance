import typing as t
from uuid import UUID

from pydantic import BaseModel, constr

RegistrationNumber = t.NewType('RegistrationNumber', constr(to_upper=True))


class GetVehicleResponse(BaseModel):
    reference: UUID
    registration_number: RegistrationNumber
    mark: str | None = None
    model: str | None = None
    region_id: int
    ts_type: int
