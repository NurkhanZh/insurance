import logging
import typing as t

from aiomisc import Service

from insurance.infrastructure.redis.client import RedlockClient

logger = logging.getLogger('redlock_client')


class RedlockService(Service):
    client: RedlockClient

    def __init__(self, host: str, port: int = 6379, db: int = 0):
        super().__init__()
        self.client = RedlockClient(host=host, port=port, db=db)

    async def start(self) -> t.Any:
        logger.info('Redlock service started')

    async def stop(self, exception: Exception = None) -> t.Any:
        await self.client.destroy(exception)
        logger.info('Redlock service stopped')
