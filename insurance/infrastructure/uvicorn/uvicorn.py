import logging
from typing import Any

import uvicorn
from aiomisc import Service
from fastapi import FastAPI


class UvicornApiService(Service):

    def __init__(self,
                 app: FastAPI,
                 host: str = '127.0.0.1',
                 port: int = 8000,
                 logger: str = 'uvicorn',
                 log_config: dict = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._host = host
        self._port = port
        self._logger = logging.getLogger(logger)
        self._log_config = log_config or uvicorn.config.LOGGING_CONFIG
        self._config = None

    @property
    def application(self):
        return self._app

    @property
    def logger(self):
        return self._logger

    def _init_config(self):
        self._config = uvicorn.Config(
            app=self._app,
            host=self._host,
            port=self._port,
            log_config=self._log_config
        )

    def _create_server(self):
        if not self._config:
            self._init_config()

        self._server = uvicorn.Server(self._config)
        if not self._server.config.loaded:
            self._server.config.load()
        self._server.lifespan = self._server.config.lifespan_class(self._server.config)
        return self._server

    async def start(self) -> Any:
        self._create_server()
        await self._server.startup()
        self.logger.info(f'{self.application.title} started')

    async def stop(self, exception: Exception = None) -> Any:
        await self._server.shutdown()
        self.logger.info(f'{self.application.title} stopped')
