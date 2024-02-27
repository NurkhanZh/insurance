from sqlalchemy import text
from insurance.gateway.exceptions.exceptions import ServiceIsNotReadyError


class HealthCheckView:
    def __init__(self, engine):
        self._engine = engine

    async def get_service_performance(self):
        async with self._engine.begin() as connection:
            healthcheck_response = await connection.execute(
                text("""
                    SELECT 1
                """)
            )
            response = healthcheck_response.one_or_none()
            if not response:
                raise ServiceIsNotReadyError()
        return
