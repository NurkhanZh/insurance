import asyncio
import typing as t

from insurance.domains.policy.abstractions import PolicyRequiredDataFacadeABC
from insurance.domains.policy.model import Policy
from insurance.domains.policy.model.required_data.bmg.factory import RequiredPolicyBMGFactory
from insurance.domains.policy.model.required_data.bmg.strategy.abstractions import (
    CheckVerifiedPhoneFunc,
    GetPersonsDataFunc,
    GetVehicleFunc,
    GetClientFunc,
    PolicyBMGStrategyABC,
)
from insurance.domains.policy.model.required_data.dto import (
    RequiredPolicyData,
)


class PolicyRequiredDataFacade(PolicyRequiredDataFacadeABC):
    def __init__(
            self,
            check_verified_phone_func: CheckVerifiedPhoneFunc,
            get_persons_func: GetPersonsDataFunc,
            get_vehicle_func: GetVehicleFunc,
            get_client_func: GetClientFunc,
    ):
        self._factory = RequiredPolicyBMGFactory(
            check_verified_phone_func=check_verified_phone_func,
            get_persons_func=get_persons_func,
            get_vehicle_func=get_vehicle_func,
            get_client_func=get_client_func,
        )

    async def check(self, policy: Policy) -> RequiredPolicyData:
        return await self._check_bmg(policy)

    async def ensure_verified(self, policy: Policy):
        await self._ensure_bmg(policy)

    async def _check_bmg(self, policy: Policy):
        policy_state = policy.state
        insurer_strategy = self._factory.get_insurer_strategy(policy_state.product, policy_state.insurance)
        driver_strategy = self._factory.get_drivers_strategy(policy_state.product, policy_state.insurance)
        response = {}
        for coro in asyncio.as_completed((
                self._check_by_strategy(insurer_strategy, policy),
                self._check_by_strategy(driver_strategy, policy),
        )):
            response.update(await coro)

        return RequiredPolicyData.model_validate(response)

    async def _ensure_bmg(self, policy: Policy) -> None:
        policy_state = policy.state
        insurer_strategy = self._factory.get_insurer_strategy(policy_state.product, policy_state.insurance)
        driver_strategy = self._factory.get_drivers_strategy(policy_state.product, policy_state.insurance)
        await asyncio.gather(
            self._ensure_by_strategy(insurer_strategy, policy),
            self._ensure_by_strategy(driver_strategy, policy),
        )

    @staticmethod
    async def _check_by_strategy(strategy: PolicyBMGStrategyABC, policy: Policy) -> t.Mapping:
        if await strategy.required_check(policy):
            return await strategy.check(policy)
        return {}

    @staticmethod
    async def _ensure_by_strategy(strategy: PolicyBMGStrategyABC, policy: Policy) -> None:
        if await strategy.required_check(policy):
            await strategy.ensure(policy)
