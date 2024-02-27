import datetime as dt
import json
import typing as t
from decimal import Decimal
from types import MappingProxyType
from uuid import UUID

from insurance.domains.policy.dto import (
    Structure, InsuranceState, ProductTypeEnum, InsuranceNameEnum, PaymentTypeEnum,
    PolicyStatusEnum, PrevPolicy, PolicyLead, PolicyCreator, Insurer, Period, PeriodTypeEnum, StatusHistory,
    DocumentCollection, Document, DocumentType, DocumentStatus
)
from insurance.domains.policy.model import Policy, PolicyState


class Converter:

    @classmethod
    def create_policy(cls, policy: Policy) -> dict:
        state = policy.state
        return dict(
            reference=state.reference,
            product=state.product.value,
            insurance=state.insurance.value,
            channel=state.channel,
            phone=state.phone,
            prev_global_id=state.prev_global_id,
            downloaded=state.downloaded,
            premium=state.premium,
            cost=state.cost,
            reward=state.reward,
            retention_reward=state.retention_reward,
            conditions=state.conditions,
            status=state.status.value,
            attributes=json.dumps(dict(state.attributes)),
            lead_reference=state.lead.reference,
            creator_reference=state.creator.reference,
            period_type=state.period.type.value,
            period_value=state.period.value,
            actual_insurance_state=state.actual_insurance_state.reference,
            created_time=state.created_time,
            updated_time=state.updated_time,
            version=1,
        )

    @classmethod
    def create_insurance_state(cls, policy_reference: UUID, insurance_state: InsuranceState, period: Period):
        return dict(reference=insurance_state.reference,
                    policy_reference=policy_reference,
                    begin_date=insurance_state.begin_date,
                    end_date=period.end_date(insurance_state.begin_date),
                    email=insurance_state.email,
                    payment_type=insurance_state.payment_type.value,
                    redirect_url=insurance_state.redirect_url,
                    insurance_reference=insurance_state.insurance_reference,
                    global_id=insurance_state.global_id,
                    status=insurance_state.status.value)

    @classmethod
    def create_documents(cls, document_collection: DocumentCollection, insurance_state_reference: UUID) -> t.List[dict]:
        return [
            dict(
                reference=document.reference,
                insurance_state_reference=insurance_state_reference,
                type=document.document_type.value,
                status=document.status.value
            )
            for document in document_collection.documents
        ]

    @classmethod
    def get_policy(cls, policy_data) -> Policy:
        prev_policy = None
        if policy_data.prev_global_id:
            prev_policy = PrevPolicy(prev_global_id=policy_data.prev_global_id,
                                     insurance=InsuranceNameEnum(policy_data.insurance))
        retention_reward = Decimal(policy_data.retention_reward) if policy_data.retention_reward is not None else None
        structure = [Structure(**structure) for structure in policy_data.structure]
        insurance_states = cls.parse_insurance_state(policy_data.insurance_states)
        state = PolicyState.restore(
            reference=policy_data.reference,
            product=ProductTypeEnum(policy_data.product),
            insurance=InsuranceNameEnum(policy_data.insurance),
            status=PolicyStatusEnum(policy_data.status),
            channel=policy_data.channel,
            phone=policy_data.phone,
            prev_policy=prev_policy,
            downloaded=policy_data.downloaded,
            premium=policy_data.premium,
            cost=policy_data.cost,
            reward=Decimal(policy_data.reward),
            retention_reward=retention_reward,
            conditions=tuple(policy_data.conditions),
            attributes=MappingProxyType(policy_data.attributes),
            structure=structure,
            insurer=Insurer(**policy_data.insurer),
            lead=PolicyLead(reference=policy_data.lead_reference),
            creator=PolicyCreator(reference=policy_data.creator_reference),
            period=Period(type=PeriodTypeEnum(policy_data.period_type), value=policy_data.period_value),
            actual_insurance_state_reference=policy_data.actual_insurance_state,
            status_records=[],
            insurance_states=insurance_states,
            created_time=policy_data.created_time,
            updated_time=policy_data.updated_time,
        )
        policy = Policy.restore(state)
        setattr(policy, '__version', policy_data.version)
        return policy

    @classmethod
    def parse_insurance_state(cls, insurance_states: list[dict]) -> list[InsuranceState]:
        return [
            InsuranceState(
                begin_date=dt.date.fromisoformat(state['begin_date']),
                email=state['email'],
                payment_type=PaymentTypeEnum(state['payment_type']),
                status=PolicyStatusEnum(state['status']),
                redirect_url=state['redirect_url'],
                insurance_reference=state['insurance_reference'],
                global_id=state['global_id'],
                status_history=StatusHistory(),
                reference=UUID(state['reference']),
                document_collection=cls._parse_document_collection(state['document_collection'])
            )
            for state in insurance_states
        ]

    @classmethod
    def _parse_document_collection(cls, document_collection: list[dict]) -> DocumentCollection:
        return DocumentCollection(
            documents=[
                Document(
                    reference=UUID(document['reference']),
                    document_type=DocumentType(document['type']),
                    status=DocumentStatus(document['status']),
                )
                for document in document_collection
            ]
        )


    @classmethod
    def update_policy(cls, policy: Policy) -> dict:
        state = policy.state
        return dict(reference=policy.reference,
                    downloaded=state.downloaded,
                    premium=state.premium,
                    cost=state.cost,
                    reward=state.reward,
                    retention_reward=str(state.retention_reward) if state.retention_reward is not None else None,
                    status=state.status.value,
                    conditions=state.conditions,
                    attributes=json.dumps(dict(state.attributes)),
                    actual_insurance_state_ref=state.actual_insurance_state.reference,
                    version=getattr(policy, '__version', None))
