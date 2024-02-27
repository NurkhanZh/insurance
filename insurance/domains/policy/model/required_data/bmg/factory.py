import typing as t

from insurance.domains.policy.dto import ProductTypeEnum, InsuranceNameEnum
from insurance.domains.policy.model.required_data.bmg.strategy.abstractions import (
    PolicyBMGStrategyABC,
    GetVehicleFunc,
    GetPersonsDataFunc,
    GetClientFunc,
    CheckVerifiedPhoneFunc,
)
from .strategy.default import DefaultPolicyBMGStrategy
from .strategy.eurasia import EurasiaOsgpoDriversBMGStrategy, EurasiaOsgpoInsurerBMGStrategy


INSURANCE: t.TypeAlias = str
PRODUCT: t.TypeAlias = str


class RequiredPolicyBMGFactory:
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

    def get_insurer_strategy(self, product: ProductTypeEnum, insurance: InsuranceNameEnum) -> PolicyBMGStrategyABC:
        match product, insurance:
            case ProductTypeEnum.OSGPO_VTS, InsuranceNameEnum.EURASIA:
                return EurasiaOsgpoInsurerBMGStrategy(
                    get_persons_func=self._get_persons_func,
                    get_vehicle_func=self._get_vehicle_func,
                    get_client_func=self._get_client_func,
                    check_verified_phone_func=self._check_verified_phone_func,
                )
            case _:
                return DefaultPolicyBMGStrategy()

    def get_drivers_strategy(self, product: ProductTypeEnum, insurance: InsuranceNameEnum) -> PolicyBMGStrategyABC:
        match product, insurance:
            case ProductTypeEnum.OSGPO_VTS, InsuranceNameEnum.EURASIA:
                return EurasiaOsgpoDriversBMGStrategy(
                    get_persons_func=self._get_persons_func,
                    get_vehicle_func=self._get_vehicle_func,
                    check_verified_phone_func=self._check_verified_phone_func,
                )
            case _:
                return DefaultPolicyBMGStrategy()

