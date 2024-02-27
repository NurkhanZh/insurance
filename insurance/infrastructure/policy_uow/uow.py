from dddmisc.unit_of_work import AbstractAsyncUnitOfWork
from sqlalchemy.ext.asyncio import AsyncEngine


class UOW(AbstractAsyncUnitOfWork):
    async def _begin_transaction(self, factory: AsyncEngine) -> AsyncEngine:
        return factory

    async def _commit_transaction(self, *args, **kwargs):
        pass

    async def _rollback_transaction(self, *args, **kwargs):
        pass
