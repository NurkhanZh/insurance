from enum import Enum


class InsuranceNameEnum(str, Enum):
    EURASIA = "eurasia"
    JUSAN = "jgarant"
    INTERTEACH = "interteach"
    BASEL = "basel"
    FFINS = "ffins"
    HALYK = "halyk"

    @classmethod
    def _missing_(cls, value: str):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member

    def __str__(self):
        return self.value


class ProductTypeEnum(str, Enum):
    OSGPO_VTS = 'osgpo-vts'
    CASCO_LIMIT = 'casco-limit'

    @classmethod
    def _missing_(cls, value: str):
        value = value.lower().replace('_', '-')
        for member in cls:
            if member.value == value:
                return member

    def __str__(self):
        return self.value


class PaymentTypeEnum(int, Enum):
    WITH_OUT_ANY_PAY = 0
    WITH_ANY_PAY = 1
    ONLY_ANY_PAY = 2


class PolicyStatusEnum(str, Enum):
    DRAFT = 'DRAFT'
    WAIT_CALLBACK = 'WAIT_CALLBACK'
    PAYED = 'PAYED'
    COMPLETED_IN_INSURANCE = 'COMPLETED_IN_INSURANCE'
    COMPLETED = 'COMPLETED'
    RESCINDED = 'RESCINDED'
    REISSUED = 'REISSUED'
    RESTORED = 'RESTORED'
    OPERATOR_ERROR = 'OPERATOR_ERROR'


class PeriodTypeEnum(str, Enum):
    YEAR = 'year'
    MONTH = 'month'
    DAY = 'day'


class DocumentType(str, Enum):
    ACCRUE = 'ACCRUE'
    RETENTION = 'RETENTION'
    CANCEL_RETENTION = 'CANCEL_RETENTION'


class DocumentStatus(str, Enum):
    CREATED = 'CREATED'
    CONFIRMED = 'CONFIRMED'
    CANCELED = 'CANCELED'
