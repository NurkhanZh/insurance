import logging
import typing as t

from aiomisc import Service
from dddmisc import AsyncMessageBus

logger = logging.getLogger('message_bus_logger')


class MessageBusService(Service):
    def __init__(self, message_bus: AsyncMessageBus, **kwargs):
        self.message_bus = message_bus
        super().__init__(**kwargs)

    async def start(self) -> t.Any:
        logger.info("MessageBusService starting...")
        self.message_bus.set_loop(self.loop)
        await self.message_bus.start()
        logger.info("MessageBusService started")

    async def stop(self, exception: Exception = None):
        logger.info("MessageBusService stopping...")
        await self.message_bus.stop()
        if self.message_bus._default_engine is not None:
            await self.message_bus._default_engine.dispose(close=True)
        logger.info("MessageBusService stopped...")
