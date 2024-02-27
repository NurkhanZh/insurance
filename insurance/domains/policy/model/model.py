import datetime as dt
import typing as t
from uuid import UUID
from copy import copy, deepcopy

from dddmisc import BaseAggregate

from insurance.domains.policy.dto import (
    InsuranceNameEnum, Lead, InsuranceOffer, PolicyStatusEnum, PaymentTypeEnum, StatusInfo, Document
)
from insurance.domains.policy.events.events import UpdatePolicyStatusEvent
from insurance.domains.policy.exceptions import InsuranceNotCorrectError, LeadMustBeFreeze
from insurance.domains.policy.model.model_state import PolicyState
from insurance.domains.policy.model.policy_states import (
    DraftState, WaitCallbackState, PayedPolicyState, CompletedInInsurancePolicyState, CompletedPolicyState,
    OperatorErrorPolicyState, RescindedPolicyState, ReissuedPolicyState, RestoredPolicyState,
    CreateAccrueRewardPolicyState, CancelRetentionRewardPolicyState,
    ConfirmAccrueRewardPolicyState, CreateRetentionRewardPolicyState,
    ConfirmRetentionRewardPolicyState, CancelAccrueRewardPolicyState
)
from insurance.domains.policy.model.product_validators import PolicyProductABC


class Policy(BaseAggregate):
    _state: PolicyState = None

    @classmethod
    def create(cls, lead: Lead, offer: InsuranceOffer, insurance: InsuranceNameEnum) -> 'Policy':
        obj = cls()
        if lead.prev_policy and lead.prev_policy.insurance != insurance:
            raise InsuranceNotCorrectError()
        if not lead.is_freeze:
            raise LeadMustBeFreeze()
        obj._state = PolicyState.create(lead=lead, offer=offer, insurance=insurance)
        begin_date = PolicyProductABC.get(lead.product_code).get_default_begin_date()
        DraftState(begin_date=begin_date, email='', payment_type=PaymentTypeEnum.WITH_OUT_ANY_PAY).apply(obj._state)

        return obj

    @classmethod
    def restore(cls, state: PolicyState) -> 'Policy':
        obj = cls()
        obj._state = state

        return obj

    @property
    def state(self) -> 'PolicyState':
        cp_state: PolicyState = copy(self._state)
        cp_state.insurance_states = deepcopy(self._state.insurance_states)
        cp_state.actual_insurance_state = cp_state.insurance_states.get_by_reference(
            self._state.actual_insurance_state.reference
        )
        cp_state.status_history = deepcopy(self._state.status_history)

        return cp_state

    @property
    def reference(self) -> UUID:
        return self._state.reference

    @property
    def accrue_reward_document(self) -> t.Optional[Document]:
        return self._state.actual_insurance_state.get_accrue_reward_document()

    @property
    def retention_reward_document(self) -> t.Optional[Document]:
        return self._state.actual_insurance_state.get_retention_reward_document()

    def update_policy(self,
                      begin_date: t.Optional[dt.date],
                      email: t.Optional[str],
                      payment_type: t.Optional[PaymentTypeEnum]):
        draft_state = DraftState(begin_date=begin_date, email=email, payment_type=payment_type)
        draft_state.apply(self._state)
        self._add_events()

    def set_insurance_info(self, insurance_reference, redirect_url: str):
        WaitCallbackState(insurance_reference=insurance_reference, redirect_url=redirect_url).apply(self._state)
        self._add_events()

    def update_status(self, status_info: StatusInfo):
        match status_info.status_type:
            case PolicyStatusEnum.PAYED:
                status_state = PayedPolicyState(status_info=status_info)
            case PolicyStatusEnum.COMPLETED_IN_INSURANCE:
                status_state = CompletedInInsurancePolicyState(status_info=status_info)
            case PolicyStatusEnum.OPERATOR_ERROR:
                status_state = OperatorErrorPolicyState(status_info=status_info)
            case PolicyStatusEnum.RESCINDED:
                status_state = RescindedPolicyState(status_info=status_info)
            case PolicyStatusEnum.REISSUED:
                status_state = ReissuedPolicyState(status_info=status_info)
            case PolicyStatusEnum.RESTORED:
                status_state = RestoredPolicyState(status_info=status_info)
            case _:
                raise ValueError(f'Policy unknown status to update. Status: {status_info.status_type}')
        status_state.apply(self._state)
        self._add_events()

    def update_offer(self, offer: InsuranceOffer, insurance_reference: str):
        CompletedPolicyState(offer=offer, insurance_reference=insurance_reference).apply(self._state)
        self._add_events()

    def set_pdf_downloaded(self):
        self._state.downloaded = True
        self.add_aggregate_event(UpdatePolicyStatusEvent(reference=self.reference, channel_id=self._state.channel))

    def create_accrue_reward(self, insurance_reference: str, document_reference: UUID):
        state = CreateAccrueRewardPolicyState(insurance_reference=insurance_reference,
                                              document_reference=document_reference)
        state.apply(self._state)
        self._add_events()

    def cancel_accrue_reward(self, insurance_reference: str):
        state = CancelAccrueRewardPolicyState(insurance_reference=insurance_reference)
        state.apply(self._state)

    def confirm_accrue_reward(self, insurance_reference: str):
        state = ConfirmAccrueRewardPolicyState(insurance_reference=insurance_reference)
        state.apply(self._state)

    def create_retention_reward(self, insurance_reference: str, document_reference: UUID):
        state = CreateRetentionRewardPolicyState(insurance_reference=insurance_reference,
                                                 document_reference=document_reference)
        state.apply(self._state)
        self._add_events()

    def confirm_retention_reward(self, insurance_reference: str):
        state = ConfirmRetentionRewardPolicyState(insurance_reference=insurance_reference)
        state.apply(self._state)

    def cancel_retention_reward(self, insurance_reference: str):
        state = CancelRetentionRewardPolicyState(insurance_reference=insurance_reference)
        state.apply(self._state)

    def _add_events(self):
        for ev in self._state.get_events():
            self.add_aggregate_event(event=ev)
        self._state.empty_events()
