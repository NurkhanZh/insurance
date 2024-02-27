import typing as t
import datetime as dt
from types import MappingProxyType
from uuid import UUID, uuid4
from decimal import Decimal

from dddmisc import DDDEvent

from insurance.domains.policy.dto import (
    ProductTypeEnum, InsuranceNameEnum, StatusHistory, Period, Structure, Insurer, Lead, InsuranceOffer, StatusRecord,
    PolicyStatusEnum, PaymentTypeEnum, InsuranceState, PrevPolicy, PolicyCreator, PolicyLead, Document
)
from insurance.domains.policy.events.events import UpdatePolicyStatusEvent


class InsuranceStateCollection:
    def __init__(self):
        self._states: list[InsuranceState] = []

    @property
    def states(self) -> t.Tuple[InsuranceState]:
        return tuple([state for state in self._states])

    def set_insurance_states(self, *states: InsuranceState):
        for state in states:
            self.add(state)

    def search(self, begin_date: dt.date, email: str, payment_type: PaymentTypeEnum) -> InsuranceState | None:
        return next((item for item in self._states
                     if all((item.begin_date == begin_date,
                             item.email == email,
                             item.payment_type == payment_type))), None)

    def get_by_insurance_reference(self, insurance_reference: str) -> InsuranceState | None:
        return next((state for state in self._states if state.insurance_reference == insurance_reference), None)

    def get_by_status(self, status: PolicyStatusEnum) -> InsuranceState | None:
        return next((state for state in self._states if state.status == status), None)

    def get_by_reference(self, reference: UUID) -> InsuranceState | None:
        return next((state for state in self._states if state.reference == reference), None)

    def get_by_global_id(self, global_id: str) -> InsuranceState | None:
        return next((state for state in self._states if state.global_id == global_id), None)

    def add(self, state: InsuranceState):
        self._states.append(state)


class PolicyState:
    _status: PolicyStatusEnum
    _reference: UUID
    product: ProductTypeEnum
    insurance: InsuranceNameEnum
    channel: str
    phone: str
    prev_policy: PrevPolicy
    downloaded: bool
    premium: int
    cost: int
    reward: Decimal
    retention_reward: Decimal
    conditions: t.Tuple[str]
    attributes: MappingProxyType
    structure: t.List[Structure]
    insurer: Insurer
    lead: PolicyLead
    creator: PolicyCreator
    period: Period
    status_history: StatusHistory
    insurance_states: InsuranceStateCollection
    actual_insurance_state: InsuranceState

    created_time: dt.datetime
    updated_time: dt.datetime

    _events: t.Set[DDDEvent]

    @classmethod
    def create(cls,
               lead: Lead,
               offer: InsuranceOffer,
               insurance: InsuranceNameEnum,
               reference: UUID = None) -> 'PolicyState':
        obj = cls()
        obj.parse_offer(offer)
        obj.parse_lead(lead)
        obj.insurance = insurance
        obj.retention_reward = None
        obj._status = None
        obj.downloaded = False
        obj.insurance_states = InsuranceStateCollection()
        obj.actual_insurance_state = None
        obj.status_history = StatusHistory()
        obj._reference = reference or uuid4()
        obj.created_time = dt.datetime.now()
        obj.updated_time = dt.datetime.now()
        obj._events = set()

        return obj

    @classmethod
    def restore(cls,
                reference: UUID,
                product: ProductTypeEnum,
                insurance: InsuranceNameEnum,
                status: PolicyStatusEnum,
                channel: str,
                phone: str,
                prev_policy: t.Optional[PrevPolicy],
                downloaded: bool,
                premium: int,
                cost: int,
                reward: Decimal,
                retention_reward: t.Optional[Decimal],
                conditions: t.Tuple[str],
                attributes: MappingProxyType,
                structure: t.List[Structure],
                insurer: Insurer,
                lead: PolicyLead,
                creator: PolicyCreator,
                period: Period,
                actual_insurance_state_reference: UUID,
                status_records: t.Iterable[StatusRecord],
                insurance_states: t.Iterable[InsuranceState],
                created_time: dt.datetime,
                updated_time: dt.datetime):
        obj = cls()
        obj._reference = reference
        obj.product = product
        obj.insurance = insurance
        obj._status = status
        obj.channel = channel
        obj.phone = phone
        obj.prev_policy = prev_policy
        obj.downloaded = downloaded
        obj.premium = premium
        obj.cost = cost
        obj.reward = reward
        obj.retention_reward = retention_reward
        obj.conditions = conditions
        obj.attributes = attributes
        obj.structure = structure
        obj.insurer = insurer
        obj.lead = lead
        obj.creator = creator
        obj.period = period
        obj.created_time = created_time
        obj.updated_time = updated_time
        obj.status_history = StatusHistory(*status_records)
        obj.insurance_states = InsuranceStateCollection()
        obj.insurance_states.set_insurance_states(*insurance_states)
        obj.actual_insurance_state = obj.insurance_states.get_by_reference(actual_insurance_state_reference)
        obj._events = set()

        return obj

    @property
    def reference(self):
        return self._reference

    @property
    def global_id(self):
        return self.actual_insurance_state.global_id

    @property
    def prev_global_id(self):
        return self.prev_policy.prev_global_id if self.prev_policy else None

    @property
    def end_date(self):
        return self.period.end_date(self.actual_insurance_state.begin_date)

    @property
    def email(self):
        return self.actual_insurance_state.email

    @property
    def begin_date(self):
        return self.actual_insurance_state.begin_date

    @property
    def payment_type(self):
        return self.actual_insurance_state.payment_type

    @property
    def redirect_url(self):
        return self.actual_insurance_state.redirect_url

    @property
    def insurance_reference(self):
        return self.actual_insurance_state.insurance_reference

    @property
    def status(self):
        return self._status

    def set_status(self, status: PolicyStatusEnum, timestamp: dt.datetime):
        self._status = status
        self.status_history.add_record(status=status, timestamp=timestamp)
        self.updated_time = dt.datetime.now()
        self.add_event(UpdatePolicyStatusEvent(reference=self.reference, channel_id=self.channel))

    def parse_offer(self, offer: InsuranceOffer):
        self.premium = offer.premium
        self.cost = offer.cost
        self.reward = offer.reward
        self.conditions = offer.conditions
        self.attributes = offer.attributes

    def parse_lead(self, lead: Lead):
        self.product = lead.product_code
        self.channel = lead.channel
        self.phone = lead.phone
        self.period = lead.period
        self.structure = lead.structure
        self.insurer = lead.insurer
        self.prev_policy = lead.prev_policy
        self.lead = PolicyLead(reference=lead.reference)
        self.creator = PolicyCreator(reference=lead.creator_reference)

    def update_attributes(self, extra_attrs: MappingProxyType):
        attributes = dict(self.attributes)
        attributes.update(extra_attrs)
        self.attributes = MappingProxyType(attributes)

    def add_event(self, event: DDDEvent):
        self._events.add(event)

    def empty_events(self):
        self._events = set()

    def get_events(self) -> t.Tuple[DDDEvent]:
        return tuple(ev for ev in self._events)
