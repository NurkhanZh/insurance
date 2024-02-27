import abc
import datetime as dt

from insurance.domains.policy.dto import ProductTypeEnum
from insurance.domains.policy.exceptions import InvalidBeginDateError


class PolicyProductValidatorABCMeta(abc.ABCMeta):
    _policy_products = dict()

    def __new__(cls, *args, **kwargs):
        klass = super().__new__(cls, *args, **kwargs)
        klass._register_state(klass)  # noqa

        return klass

    @classmethod
    def _register_state(cls, product_validator: 'PolicyProductABC'):
        cls._policy_products[product_validator.product] = product_validator

    def get(cls, product: ProductTypeEnum) -> 'PolicyProductABC':
        return cls._policy_products[product]


class PolicyProductABC(abc.ABC, metaclass=PolicyProductValidatorABCMeta):
    product: ProductTypeEnum = 'abstract'

    @abc.abstractmethod
    def validate_begin_date(self, begin_date: dt.date):
        """
        Validate attributes of policy state depending on product type
        :return: None
        """
    @classmethod
    @abc.abstractmethod
    def get_default_begin_date(cls) -> dt.date:
        """
        Returns valid begin date of policy by product
        :return:
        """


class _BaseOspoVtsCascoLimit:
    @classmethod
    def validate_begin_date(cls, begin_date):
        if begin_date <= dt.date.today():
            raise InvalidBeginDateError()

    @classmethod
    def get_default_begin_date(cls) -> dt.date:
        return dt.date.today() + dt.timedelta(1)


class OsgpoVtsValidator(_BaseOspoVtsCascoLimit, PolicyProductABC):
    product = ProductTypeEnum.OSGPO_VTS


class CascoLimitValidator(_BaseOspoVtsCascoLimit, PolicyProductABC):
    product = ProductTypeEnum.CASCO_LIMIT

