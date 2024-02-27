import abc
from decimal import Decimal
import datetime as dt

from insurance.domains.policy.dto import ProductTypeEnum, InsuranceNameEnum
from insurance.domains.policy.model.model_state import PolicyState


class PolicyRetentionRewardCalcABC(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def calc_operator_error_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        """
        Метод для калькуляции суммы удержания при Operator Error
        """

    @classmethod
    @abc.abstractmethod
    def calc_rescinded_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        """
        Метод для калькуляции суммы удержания при Rescinded
        """

    @classmethod
    @abc.abstractmethod
    def calc_reissued_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        """
        Метод для калькуляции суммы удержания при Reissued
        """


class BaseOGPOPolicyRefundCalc(PolicyRetentionRewardCalcABC):

    @classmethod
    def calc_operator_error_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        return state.reward

    @classmethod
    def calc_rescinded_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        return Decimal('0.00')

    @classmethod
    def calc_reissued_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        return Decimal('0.00')


class EurasiaRefundCalc(PolicyRetentionRewardCalcABC):
    NINETY_ONE_DAYS = 91

    @classmethod
    def calc_operator_error_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        return state.reward

    @classmethod
    def calc_rescinded_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        if state.reward == Decimal('0'):
            return Decimal('0.00')
        refund_amount = Decimal(state.attributes.get('refund_amount'))

        return (state.reward * (Decimal(refund_amount) / state.cost)).quantize(Decimal('0.00'))

    @classmethod
    def calc_reissued_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        if state.reward == Decimal('0'):
            return Decimal('0.00')
        days_from_creation = (operation_date - state.created_time.date()).days
        ins_condition = (days_from_creation < cls.NINETY_ONE_DAYS and
                         (state.attributes.get('with_inexperienced') or
                          state.attributes.get('region_changed')))
        if ins_condition:
            return state.reward

        return Decimal('0.00')


class PolicyRetentionRewardCalc(PolicyRetentionRewardCalcABC):
    DEFAULT = 'DEFAULT'
    PRODUCT_INSURANCE_CALC = {
        ProductTypeEnum.OSGPO_VTS: {
            DEFAULT: BaseOGPOPolicyRefundCalc,
            InsuranceNameEnum.EURASIA: EurasiaRefundCalc,
        }
    }

    @classmethod
    def calc_operator_error_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        insurance_calc = cls.PRODUCT_INSURANCE_CALC.get(state.product)
        if not insurance_calc:
            raise ValueError('Unknown request to calc_operator_error_reward')
        calc = insurance_calc.get(state.insurance, insurance_calc[cls.DEFAULT])

        return calc.calc_operator_error_reward(state=state, operation_date=operation_date)

    @classmethod
    def calc_rescinded_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        insurance_calc = cls.PRODUCT_INSURANCE_CALC.get(state.product)
        if not insurance_calc:
            raise ValueError('Unknown request to calc_rescinded_reward')
        calc = insurance_calc.get(state.insurance, insurance_calc[cls.DEFAULT])

        return calc.calc_rescinded_reward(state=state, operation_date=operation_date)

    @classmethod
    def calc_reissued_reward(cls, state: PolicyState, operation_date: dt.date) -> Decimal:
        insurance_calc = cls.PRODUCT_INSURANCE_CALC.get(state.product)
        if not insurance_calc:
            raise ValueError('Unknown request to calc_reissued_reward')
        calc = insurance_calc.get(state.insurance, insurance_calc[cls.DEFAULT])

        return calc.calc_reissued_reward(state=state, operation_date=operation_date)
