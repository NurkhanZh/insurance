import typing as t
from uuid import UUID

from insurance.domains.policy.exceptions import PolicyRequiredData
from insurance.domains.policy.model.required_data.bmg.strategy.abstractions import (
    GetVehicleFunc,
    GetPersonsDataFunc,
    CheckVerifiedPhoneFunc,
    PolicyBMGStrategyABC,
    PolicyProtocol,
)
from insurance.domains.policy.model.required_data.bmg.strategy.eurasia.dto import EurasiaOsgpoConfig


class PhoneSchema(t.TypedDict):
    required: bool
    allow_bmg: bool
    allow_otp: bool


class DriverSchema(t.TypedDict):
    reference: UUID
    phone: PhoneSchema


class RequiredDataSchema(t.TypedDict):
    drivers: t.Sequence[DriverSchema]


class EurasiaOsgpoDriversBMGStrategy(PolicyBMGStrategyABC):
    def __init__(
            self,
            get_vehicle_func: GetVehicleFunc,
            get_persons_func: GetPersonsDataFunc,
            check_verified_phone_func: CheckVerifiedPhoneFunc,
    ):
        self._get_vehicle_func = get_vehicle_func
        self._get_persons_func = get_persons_func
        self._check_verified_phone_func = check_verified_phone_func
        self._config = EurasiaOsgpoConfig()

    async def required_check(self, policy: PolicyProtocol) -> bool:
        return True

    async def check(self, policy: PolicyProtocol) -> RequiredDataSchema:
        return await self._check(policy)

    async def ensure(self, policy: PolicyProtocol) -> None:
        result = await self._check(policy)
        if result['drivers']:
            reference_list = [driver['reference'] for driver in result['drivers']]
            raise PolicyRequiredData(detail=f'Ошибка валидации BMG для {reference_list}')

    async def _check(self, policy: PolicyProtocol) -> RequiredDataSchema:
        policy_state = policy.state
        driver_data = await self._get_persons_func(
            [structure.attrs.iin for structure in policy_state.structure if structure.type == 'driver']
        )
        drivers = []
        for driver in driver_data.drivers:
            if not driver.is_valid_bmg_phone and (await self._check_required_phone(driver.iin)):
                drivers.append(DriverSchema(
                    reference=driver.reference,
                    phone=PhoneSchema(
                        allow_bmg=self._config.allow_bmg,
                        allow_otp=self._config.allow_otp,
                        required=True,
                    ),
                ))
        return RequiredDataSchema(drivers=drivers)

    async def _check_required_phone(self, iin: str):
        result = await self._check_verified_phone_func(iin, self._config.insurance)
        return not result.is_verified
