import abc


class RedLockClientABC(abc.ABC):

    @abc.abstractmethod
    async def lock(self, *args, **kwargs):
        ...
