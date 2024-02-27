import abc


class PolicyRequiredDataFacadeABC(abc.ABC):
    @abc.abstractmethod
    async def check(self, policy):
        ...

    @abc.abstractmethod
    async def ensure_verified(self, policy) -> None:
        ...
