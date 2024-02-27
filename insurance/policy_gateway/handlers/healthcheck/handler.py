from starlette.requests import Request
from insurance.gateway.schemas.base import ResponseModel


async def healthcheck_with_view(request: Request):
    data = dict(data=await request.state.healthcheck_view.get_service_performance())
    return ResponseModel(data=data)
