import logging
import typing as t

from dddmisc.exceptions.core import DDDException
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from insurance.domains.policy.exceptions.exceptions import BaseInternalServiceError, BaseError


def state_middleware(state: dict):
    async def middleware(request: Request, call_next):
        for key, value in state.items():
            setattr(request.state, key, value)
        return await call_next(request)

    return middleware


def ddd_exception_handler(request: Request, exc_group: ExceptionGroup):
    try:
        raise exc_group
    except* DDDException:
        exc = next(filter(lambda err: isinstance(err, DDDException), exc_group.exceptions))
        logging.getLogger('gateway').info(
            exc.message,
            exc_info=exc
        )
        result = JSONResponse(
            status_code=200,
            content={
                'status': "ERROR",
                'data': {},
                'exc_code': type(exc).__name__,
                'exc_data': {key: str(value) for key, value in exc.extra.items()},
                'message': exc.message,
            }
        )
    except* Exception:
        exc = exc_group.exceptions[0]
        logging.getLogger('gateway').error(
            'Internal service error',
            exc_info=exc,
            extra={'path': request.url.path}
        )
        result = JSONResponse(
            status_code=200,
            content={
                'status': "ERROR",
                'data': {'exc_cls': exc.__class__.__name__, 'detail': str(exc)},
                'exc_code': 'InternalServiceError',
                'exc_data': {},
                'message': 'Internal Service Error',
            }
        )
    return result


def base_exception_handler(request: Request, exc_group: ExceptionGroup):
    try:
        raise exc_group
    except* BaseError:
        exc = next(filter(lambda err: isinstance(err, BaseError), exc_group.exceptions))
        code = get_code_from_exception(request, exc.model())
        logging.getLogger('gateway').error(exc.message_template, exc_info=exc)
        result = JSONResponse(exc.dict(), status_code=code)
    except* Exception:
        logging.getLogger('gateway').error(
            'Internal service error',
            exc_info=exc_group,
            extra={'path': request.url.path}
        )
        result = JSONResponse(BaseInternalServiceError().dict(), status_code=500)

    return result


def get_code_from_exception(request: Request, model_class: type[BaseModel]):
    return next((code for
                 code, value in request.scope['route'].response_fields.items()
                 if value.field_info.annotation.__name__ == model_class.__name__ or
                 model_class in t.get_args(value.field_info.annotation)),
                400)


async def exception_handler(request: Request, exc_group: ExceptionGroup):
    if '/v4/' in request.url.path:
        return ddd_exception_handler(request=request, exc_group=exc_group)

    return base_exception_handler(request=request, exc_group=exc_group)
