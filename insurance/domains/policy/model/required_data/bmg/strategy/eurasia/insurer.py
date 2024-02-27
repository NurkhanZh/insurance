import typing as t

from insurance.domains.policy.exceptions import PolicyRequiredData
from insurance.domains.policy.model.required_data.bmg.strategy.abstractions import (
    PolicyBMGStrategyABC,
    GetVehicleFunc,
    PolicyProtocol,
    GetPersonsDataFunc,
    GetClientFunc,
    CheckVerifiedPhoneFunc,
)
from insurance.domains.policy.model.required_data.bmg.strategy.eurasia.dto import EurasiaOsgpoConfig


class PhoneSchema(t.TypedDict):
    required: bool
    allow_bmg: bool
    allow_otp: bool


class InsurerSchema(t.TypedDict):
    phone: PhoneSchema


class RequiredDataSchema(t.TypedDict):
    insurer: t.Optional[InsurerSchema]


class EurasiaOsgpoInsurerBMGStrategy(PolicyBMGStrategyABC):
    def __init__(
            self,
            get_vehicle_func: GetVehicleFunc,
            get_persons_func: GetPersonsDataFunc,
            get_client_func: GetClientFunc,
            check_verified_phone_func: CheckVerifiedPhoneFunc,
    ):
        self._get_vehicle_func = get_vehicle_func
        self._get_persons_func = get_persons_func
        self._get_client_func = get_client_func
        self._check_verified_phone_func = check_verified_phone_func
        self._config = EurasiaOsgpoConfig()

    async def required_check(self, policy: PolicyProtocol) -> bool:
        return True

    async def check(self, policy: PolicyProtocol) -> RequiredDataSchema:
        return await self._check(policy)

    async def ensure(self, policy: PolicyProtocol) -> None:
        result = await self._check(policy)
        if result['insurer']:
            raise PolicyRequiredData(detail=f'Ошибка валидации BMG для {policy.state.insurer.title}')

    async def _check(self, policy: PolicyProtocol) -> RequiredDataSchema:
        # todo: Тут нужно чекать в insurances-adapters set-phone с номером из полиса
        policy_state = policy.state
        insurer = await self._get_client_func(iin=None, reference=policy_state.insurer.reference)
        driver_data = await self._get_persons_func([insurer.iin])
        for driver in driver_data.drivers:
            if not driver.is_valid_bmg_phone and (await self._check_required_phone(driver.iin)):
                return RequiredDataSchema(insurer=InsurerSchema(
                    phone=PhoneSchema(
                        allow_bmg=self._config.allow_bmg,
                        allow_otp=self._config.allow_otp,
                        required=True,
                    ),
                ))
        return RequiredDataSchema(insurer=None)

    async def _check_required_phone(self, iin: str):
        result = await self._check_verified_phone_func(iin, self._config.insurance)
        return not result.is_verified
