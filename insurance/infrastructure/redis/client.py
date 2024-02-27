import logging
import typing as t

from aioredlock import Aioredlock, Lock

logger = logging.getLogger('redlock_client')


class RedlockClient:
    _lock_manager: Aioredlock = None

    def __init__(self, host: str, port: int = 6379, db: int = 0):
        self._lock_manager = Aioredlock(
            [{'host': host, 'port': port, 'db': db}],
            retry_count=300,
            retry_delay_min=0.2,
            retry_delay_max=0.2,
        )

    async def destroy(self, exception: Exception = None) -> t.Any:
        await self._lock_manager.destroy()
        logger.info('Redlock service stopped')

    async def lock(self, resource: str, lock_identifier: t.Optional[str] = None, lock_timeout: int = 60):
        return await self._lock_manager.lock(str(resource), lock_timeout, lock_identifier=lock_identifier)

    async def unlock(self, resource: str, lock_identifier: str):
        return await self._lock_manager.unlock(Lock(self, resource, lock_identifier))

    async def is_locked(self, resource_or_lock: str | Lock):
        return await self._lock_manager.is_locked(resource_or_lock)
