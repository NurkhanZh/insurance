import typing as t
from insurance.domains.policy.model.required_data.bmg.strategy.abstractions import PolicyBMGStrategyABC


class DefaultPolicyBMGStrategy(PolicyBMGStrategyABC):
    async def required_check(self, policy) -> bool:
        return False

    async def check(self, policy) -> t.Never:
        pass

    async def ensure(self, policy) -> None:
        return
