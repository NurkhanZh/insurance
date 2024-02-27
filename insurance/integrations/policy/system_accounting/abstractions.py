import abc


class SystemAccountingClientABC(abc.ABC):

    @abc.abstractmethod
    async def create_pay_reward(self, payload: dict) -> str:
        ...

    @abc.abstractmethod
    async def confirm_pay_reward(self, payload: dict):
        ...

    @abc.abstractmethod
    async def cancel_reward(self, payload: dict):
        ...

    @abc.abstractmethod
    async def create_retention_reward(self, payload: dict) -> str:
        ...

    @abc.abstractmethod
    async def confirm_retention_reward(self, payload: dict):
        ...

    @abc.abstractmethod
    async def cancel_retention_reward(self, payload: dict):
        ...

    @abc.abstractmethod
    async def aclose(self):
        ...
