import typing as t

from dddmisc.exceptions.core import DDDException
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

_ERRORS = {}


class BaseError(DDDException):
    message_template: str = ''
    example_kwargs: dict

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _ERRORS[cls.__name__] = cls

    class Meta:
        domain = 'insurance-integration'
        is_baseclass = True

    @classmethod
    def model(cls) -> t.Type[BaseModel]:
        if hasattr(cls, "example_kwargs"):
            example_message = cls.message_template.format(**cls.example_kwargs)
        else:
            example_message = cls.message_template

        model = create_model(
            f"{cls.__name__}Error",
            __module__=cls.__module__,
            code=(str, FieldInfo(title="Код ошибки", examples=[cls.__name__])),
            message=(
                str,
                FieldInfo(title="Сообщение об ошибке", examples=[example_message]),
            ),
        )
        return model

    def dict(self):
        return {"code": self.__class__.__name__, "message": str(self)}

    @classmethod
    @t.final
    def parse(cls, code, message):
        return _ERRORS.get(code)(message)


class BaseInternalServiceError(BaseError):
    # TODO rename to InternalServiceError after BaseError inherited only Exception (not DDDException)
    message_template = 'InternalServiceError'

    class Meta:
        template = "InternalServiceError"


class InsuranceNotCorrectError(BaseError):
    message_template = "Переоформление не доступно для данного СК"

    class Meta:
        template = "Переоформление не доступно для данного СК"


class LeadGetOfferError(BaseError):
    message_template = "Ошибка при получения оффера"

    class Meta:
        template = "Ошибка при получения оффера"


class LeadNotFoundError(BaseError):
    message_template = "Лид не найден"

    class Meta:
        template = "Лид не найден"


class LeadMustBeFreeze(BaseError):
    message_template = "Лид должен быть заморожен"

    class Meta:
        template = "Лид должен быть заморожен"


class InvalidBeginDateError(BaseError):
    message_template = "Не валидная дата начала полиса"

    class Meta:
        template = "Не валидная дата начала полиса"


class PolicyExpiredError(BaseError):
    message_template = "Срок жизни полиса истек"

    class Meta:
        template = "Срок жизни полиса истек"


class PolicyNotFoundError(BaseError):
    message_template = 'Полис не найден'

    class Meta:
        template = 'Полис не найден'


class SavePolicyError(BaseError):
    message_template = 'Оформление полиса невозможно. Для оформления обратитесь в филиал страховой компании'

    class Meta:
        template = 'Оформление полиса невозможно. Для оформления обратитесь в филиал страховой компании'


class PolicyRequiredData(BaseError):
    message_template = 'Недостаточно данных для сохранения полиса. {detail}'

    class Meta:
        template = 'Недостаточно данных для сохранения полиса. {detail}'
