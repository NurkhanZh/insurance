import abc
import datetime as dt
import typing as t
from uuid import UUID

from insurance.domains.policy.dto import PaymentTypeEnum, PolicyStatusEnum, StatusInfo, InsuranceOffer, InsuranceState
from insurance.domains.policy.exceptions import PolicyExpiredError
from insurance.domains.policy.model.model_state import PolicyState
from insurance.domains.policy.model.product_validators import PolicyProductABC
from insurance.domains.policy.model.retention_reward_calc import PolicyRetentionRewardCalc
from insurance.domains.policy.events.events import (
    PolicyInInsuranceCompletedEvent, PolicyReissuedEvent, PolicyRescindedEvent, PolicyRestoredEvent,
    PolicyCompletedEvent, PolicyOperatorErrorEvent, PolicyAccrueRewardCreatedEvent, PolicyRetentionRewardCreatedEvent
)


class PolicyStateABC(abc.ABC):
    ALLOWED_STATUSES: tuple[PolicyStatusEnum]

    @abc.abstractmethod
    def apply(self, state: PolicyState):
        ...

    def policy_change_validate(self, state: PolicyState):
        if state.status not in self.ALLOWED_STATUSES:
            raise ValueError(f'Not allowed status change from {state.status} to {self.__class__.__name__}')


class DraftState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.DRAFT, PolicyStatusEnum.WAIT_CALLBACK, None)

    def __init__(self,
                 begin_date: t.Optional[dt.date],
                 email: t.Optional[str],
                 payment_type: t.Optional[PaymentTypeEnum]):
        self._begin_date = begin_date
        self._email = email
        self._payment_type = payment_type

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        PolicyProductABC.get(state.product).validate_begin_date(self._begin_date or state.begin_date)
        insurance_state = self._get_insurance_state(state)
        if state.status == insurance_state.status:
            return

        state.actual_insurance_state = insurance_state
        state.set_status(status=insurance_state.status, timestamp=dt.datetime.now())

    def policy_change_validate(self, state: PolicyState):
        """
        TODO check in psql. Issue: psql writes datetime in utc. Need to check after reading from db it correctly works
        Approximate solution need to convert datetime in a db to local time by adding +6h after reading
        """
        super().policy_change_validate(state)
        if state.created_time.date() != dt.date.today():
            raise PolicyExpiredError()

    def _get_insurance_state(self, state: PolicyState):
        begin_date = self._begin_date or state.begin_date
        email = state.email if self._email is None else self._email
        payment_type = state.payment_type if self._payment_type is None else self._payment_type
        if ins_state := state.insurance_states.search(begin_date, email, payment_type):
            insurance_state = ins_state
        elif ins_state := state.insurance_states.get_by_status(PolicyStatusEnum.DRAFT):
            insurance_state = ins_state
            insurance_state.begin_date = begin_date
            insurance_state.email = email
            insurance_state.payment_type = payment_type
        else:
            insurance_state = InsuranceState(begin_date, email, payment_type)
            state.insurance_states.add(insurance_state)

        return insurance_state


class WaitCallbackState(PolicyStateABC):
    ALLOWED_STATUSES = [PolicyStatusEnum.DRAFT, PolicyStatusEnum.WAIT_CALLBACK]

    def __init__(self, insurance_reference: str, redirect_url: str):
        self._insurance_reference = insurance_reference
        self._redirect_url = redirect_url

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        state.actual_insurance_state.insurance_reference = self._insurance_reference
        state.actual_insurance_state.redirect_url = self._redirect_url
        state.actual_insurance_state.set_status(status=PolicyStatusEnum.WAIT_CALLBACK, timestamp=dt.datetime.now())
        if state.status == PolicyStatusEnum.WAIT_CALLBACK:
            return

        state.set_status(status=PolicyStatusEnum.WAIT_CALLBACK, timestamp=dt.datetime.now())

    def policy_change_validate(self, state: PolicyState):
        super().policy_change_validate(state)
        if state.created_time.date() != dt.date.today():
            raise PolicyExpiredError()


class BaseUpdateStatusPolicy:
    _status_info: StatusInfo

    def __init__(self, status_info: StatusInfo):
        self._status_info = status_info


class PayedPolicyState(BaseUpdateStatusPolicy, PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.DRAFT,
                        PolicyStatusEnum.WAIT_CALLBACK,
                        PolicyStatusEnum.PAYED,
                        PolicyStatusEnum.COMPLETED_IN_INSURANCE,
                        PolicyStatusEnum.COMPLETED)

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._status_info.insurance_reference)
        if state.status in [PolicyStatusEnum.COMPLETED_IN_INSURANCE, PolicyStatusEnum.COMPLETED]:
            state.status_history.add_record(status=PolicyStatusEnum.PAYED, timestamp=self._status_info.timestamp)
            ins_state.status_history.add_record(status=PolicyStatusEnum.PAYED, timestamp=self._status_info.timestamp)
            return

        ins_state.set_status(status=PolicyStatusEnum.PAYED, timestamp=self._status_info.timestamp)
        if state.status == PolicyStatusEnum.PAYED:
            return

        state.actual_insurance_state = ins_state
        state.set_status(status=PolicyStatusEnum.PAYED, timestamp=self._status_info.timestamp)


class CompletedInInsurancePolicyState(BaseUpdateStatusPolicy, PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.DRAFT,
                        PolicyStatusEnum.WAIT_CALLBACK,
                        PolicyStatusEnum.PAYED,
                        PolicyStatusEnum.COMPLETED_IN_INSURANCE)

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._status_info.insurance_reference)
        ins_state.set_status(status=PolicyStatusEnum.COMPLETED_IN_INSURANCE, timestamp=self._status_info.timestamp)
        ins_state.global_id = self._status_info.global_id
        if state.status == PolicyStatusEnum.COMPLETED_IN_INSURANCE:
            return

        state.actual_insurance_state = ins_state
        state.set_status(status=PolicyStatusEnum.COMPLETED_IN_INSURANCE, timestamp=self._status_info.timestamp)
        ev = PolicyInInsuranceCompletedEvent(reference=state.reference,
                                             insurance_reference=self._status_info.insurance_reference)
        state.add_event(ev)


class CompletedPolicyState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.COMPLETED_IN_INSURANCE, PolicyStatusEnum.COMPLETED)

    def __init__(self, offer: InsuranceOffer, insurance_reference: str):
        self._offer = offer
        self._insurance_reference = insurance_reference

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._insurance_reference)
        ins_state.set_status(status=PolicyStatusEnum.COMPLETED, timestamp=dt.datetime.now())
        if state.status == PolicyStatusEnum.COMPLETED:
            return

        state.parse_offer(offer=self._offer)
        state.actual_insurance_state = ins_state
        state.set_status(status=PolicyStatusEnum.COMPLETED, timestamp=dt.datetime.now())
        ev = PolicyCompletedEvent(reference=state.reference, insurance_reference=state.insurance_reference)
        state.add_event(ev)


class OperatorErrorPolicyState(BaseUpdateStatusPolicy, PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.COMPLETED,
                        PolicyStatusEnum.COMPLETED_IN_INSURANCE,
                        PolicyStatusEnum.RESTORED)

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_global_id(global_id=self._status_info.global_id)
        ins_state.set_status(status=PolicyStatusEnum.OPERATOR_ERROR, timestamp=self._status_info.timestamp)
        retention_reward = PolicyRetentionRewardCalc.calc_operator_error_reward(
            state=state, operation_date=self._status_info.timestamp.date()
        )
        state.retention_reward = retention_reward
        ins_state = state.insurance_states.get_by_status(PolicyStatusEnum.COMPLETED) or ins_state
        state.actual_insurance_state = ins_state
        state.set_status(status=ins_state.status, timestamp=self._status_info.timestamp)
        if state.status == PolicyStatusEnum.OPERATOR_ERROR:
            ev = PolicyOperatorErrorEvent(reference=state.reference, insurance_reference=state.insurance_reference)
            state.add_event(ev)


class RescindedPolicyState(BaseUpdateStatusPolicy, PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.COMPLETED, PolicyStatusEnum.RESTORED)

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_global_id(global_id=self._status_info.global_id)
        ins_state.set_status(status=PolicyStatusEnum.RESCINDED, timestamp=self._status_info.timestamp)
        state.update_attributes(extra_attrs=self._status_info.extra_attrs)
        retention_reward = PolicyRetentionRewardCalc.calc_rescinded_reward(
            state=state, operation_date=self._status_info.timestamp.date()
        )
        state.retention_reward = retention_reward
        ins_state = state.insurance_states.get_by_status(PolicyStatusEnum.COMPLETED) or ins_state
        state.actual_insurance_state = ins_state
        state.set_status(status=ins_state.status, timestamp=self._status_info.timestamp)
        if state.status == PolicyStatusEnum.RESCINDED:
            ev = PolicyRescindedEvent(reference=state.reference, insurance_reference=state.insurance_reference)
            state.add_event(ev)


class ReissuedPolicyState(BaseUpdateStatusPolicy, PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.COMPLETED, PolicyStatusEnum.RESTORED)

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_global_id(global_id=self._status_info.global_id)
        ins_state.set_status(status=PolicyStatusEnum.REISSUED, timestamp=self._status_info.timestamp)
        state.update_attributes(extra_attrs=self._status_info.extra_attrs)
        retention_reward = PolicyRetentionRewardCalc.calc_reissued_reward(
            state=state, operation_date=self._status_info.timestamp.date()
        )
        state.retention_reward = retention_reward
        state.actual_insurance_state = ins_state
        state.set_status(status=ins_state.status, timestamp=self._status_info.timestamp)
        if state.status == PolicyStatusEnum.REISSUED:
            ev = PolicyReissuedEvent(reference=state.reference, insurance_reference=state.insurance_reference)
            state.add_event(ev)


class RestoredPolicyState(BaseUpdateStatusPolicy, PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.REISSUED,)

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_global_id(global_id=self._status_info.global_id)
        ins_state.set_status(status=PolicyStatusEnum.RESTORED, timestamp=self._status_info.timestamp)
        state.update_attributes(extra_attrs=self._status_info.extra_attrs)
        state.actual_insurance_state = ins_state
        state.set_status(status=ins_state.status, timestamp=self._status_info.timestamp)
        if state.status == PolicyStatusEnum.RESTORED:
            ev = PolicyRestoredEvent(reference=state.reference, insurance_reference=state.insurance_reference)
            state.add_event(ev)


class CreateAccrueRewardPolicyState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.COMPLETED,)

    def __init__(self, insurance_reference: str, document_reference: UUID):
        self._insurance_reference = insurance_reference
        self._document_reference = document_reference

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._insurance_reference)
        if not ins_state.get_accrue_reward_document():
            ins_state.create_accrue_reward(document_reference=self._document_reference)
            state.updated_time = dt.datetime.now()
            ev = PolicyAccrueRewardCreatedEvent(reference=state.reference,
                                                insurance_reference=state.insurance_reference)
            state.add_event(ev)


class ConfirmAccrueRewardPolicyState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.COMPLETED,)

    def __init__(self, insurance_reference: str):
        self._insurance_reference = insurance_reference

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._insurance_reference)
        document = ins_state.get_accrue_reward_document()
        if document and document.is_created:
            ins_state.confirm_accrue_reward()
            state.updated_time = dt.datetime.now()


class CancelAccrueRewardPolicyState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.OPERATOR_ERROR,)

    def __init__(self, insurance_reference: str):
        self._insurance_reference = insurance_reference

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._insurance_reference)
        document = ins_state.get_accrue_reward_document()
        if document and document.is_confirmed:
            ins_state.cancel_accrue_reward()
            state.updated_time = dt.datetime.now()


class CreateRetentionRewardPolicyState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.RESCINDED, PolicyStatusEnum.REISSUED)

    def __init__(self, insurance_reference: str, document_reference: UUID):
        self._insurance_reference = insurance_reference
        self._document_reference = document_reference

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._insurance_reference)
        if not ins_state.get_retention_reward_document():
            ins_state.create_retention_reward(document_reference=self._document_reference)
            state.updated_time = dt.datetime.now()
            ev = PolicyRetentionRewardCreatedEvent(reference=state.reference,
                                                   insurance_reference=state.insurance_reference)
            state.add_event(ev)


class ConfirmRetentionRewardPolicyState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.RESCINDED, PolicyStatusEnum.REISSUED)

    def __init__(self, insurance_reference: str):
        self._insurance_reference = insurance_reference

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._insurance_reference)
        document = ins_state.get_retention_reward_document()
        if document and document.is_created:
            ins_state.confirm_retention_reward()
            state.updated_time = dt.datetime.now()


class CancelRetentionRewardPolicyState(PolicyStateABC):
    ALLOWED_STATUSES = (PolicyStatusEnum.RESTORED,)

    def __init__(self, insurance_reference: str):
        self._insurance_reference = insurance_reference

    def apply(self, state: PolicyState):
        self.policy_change_validate(state)
        ins_state = state.insurance_states.get_by_insurance_reference(self._insurance_reference)
        document = ins_state.get_retention_reward_document()
        if document and document.is_confirmed:
            ins_state.cancel_retention_reward()
            state.updated_time = dt.datetime.now()
