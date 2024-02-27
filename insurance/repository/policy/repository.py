import typing as t
from uuid import UUID

from dddmisc import AbstractAsyncRepository, decorators

from insurance.domains.policy.abstractions import PolicyRepositoryABC
from insurance.domains.policy.dto import InsuranceState, StatusRecord, Insurer, Structure
from insurance.domains.policy.exceptions import PolicyNotFoundError, PolicyAlreadyUpdatedError
from insurance.domains.policy.model import Policy, PolicyState
from insurance.repository.policy.converter import Converter
from insurance.repository.policy.statement import Statement


class PolicyRepository(AbstractAsyncRepository, PolicyRepositoryABC):
    aggregate_class = Policy

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stored = set()

    @decorators.agetter
    async def get(self, reference: UUID) -> Policy:
        async with self._connection.begin() as conn:
            cursor = await conn.execute(Statement.get_policy, dict(reference=reference))
        policy_data = cursor.fetchone()
        if not policy_data:
            raise PolicyNotFoundError()

        policy = Converter.get_policy(policy_data)
        self._stored.add(policy)
        return policy

    @get.filter
    def _get_filter(self, aggregator: Policy, reference: UUID):
        return aggregator.reference == reference

    async def get_reference_by_insurance_reference(self, insurance_reference: str) -> UUID:
        async with self._connection.begin() as conn:
            cursor = await conn.execute(Statement.get_policy_reference_by_insurance_reference,
                                        dict(insurance_reference=insurance_reference))
        insurance_data = cursor.fetchone()
        if not insurance_data:
            raise PolicyNotFoundError()

        return insurance_data.policy_reference

    async def _add_to_storage(self, policy: Policy):
        if policy in self._stored:
            await self._update_policy(policy)
        else:
            await self._create_policy(policy)
        self._stored.add(policy)

    async def _create_policy(self, policy: Policy):
        policy_state = policy.state
        await self._create_policy_record(policy)
        await self._create_or_update_insurance_state(policy_state)
        await self._create_insurer(policy_reference=policy.reference, insurer=policy_state.insurer)
        await self._create_structure(policy_reference=policy.reference, list_structure=policy_state.structure)

    async def _create_policy_record(self, policy: Policy):
        data = Converter.create_policy(policy)
        stmt = Statement.insert_policy
        async with self._connection.begin() as conn:
            await conn.execute(stmt, data)
        records = policy.state.status_history.records
        if not records:
            return
        await self._create_policy_status_records(policy_reference=policy.reference, records=records)

    async def _create_or_update_insurance_state(self, policy_state: PolicyState):
        insurance_state_data = []
        documents_data = []
        for insurance_state in policy_state.insurance_states.states:
            insurance_state_data.append(
                Converter.create_insurance_state(
                    policy_reference=policy_state.reference,
                    insurance_state=insurance_state,
                    period=policy_state.period
                )
            )
            documents_data.extend(
                Converter.create_documents(
                    document_collection=insurance_state.document_collection,
                    insurance_state_reference=insurance_state.reference,
                )
            )
        stmt = Statement.insert_or_update_insurance_state
        async with self._connection.begin() as conn:
            await conn.execute(stmt, insurance_state_data)
        for insurance_state in policy_state.insurance_states.states:
            if insurance_state.status_history.records:
                await self._create_insurance_state_status_record(insurance_state_reference=insurance_state.reference,
                                                                 records=insurance_state.status_history.records)
        if documents_data:
            stmt = Statement.insert_or_update_document
            async with self._connection.begin() as conn:
                await conn.execute(stmt, documents_data)

    async def _create_insurer(self, policy_reference: UUID, insurer: Insurer):
        async with self._connection.begin() as conn:
            await conn.execute(
                Statement.insert_policy_insurer,
                dict(reference=insurer.reference,
                     policy_reference=policy_reference,
                     is_privileged=insurer.is_privileged,
                     title=insurer.title
                     )
            )

    async def _create_policy_status_records(self, policy_reference: UUID, records: t.List[StatusRecord]):
        data = [dict(status=record.status,
                     timestamp=record.timestamp,
                     policy_reference=policy_reference) for record in records]
        async with self._connection.begin() as conn:
            await conn.execute(Statement.insert_policy_status_record, data)

    async def _create_insurance_state_status_record(self,
                                                    insurance_state_reference: UUID,
                                                    records: t.List[StatusRecord]):
        data = [dict(status=record.status,
                     timestamp=record.timestamp,
                     insurance_state_reference=insurance_state_reference) for record in records]
        async with self._connection.begin() as conn:
            await conn.execute(Statement.insert_insurance_state_status_record, data)

    async def _create_structure(self, policy_reference: UUID, list_structure: t.List[Structure]):
        data = [dict(policy_reference=str(policy_reference),
                     item_reference=strct.item_reference,
                     type=strct.type,
                     title=strct.title,
                     attrs=strct.attrs.model_dump_json(),
                     ) for strct in list_structure]
        async with self._connection.begin() as conn:
            await conn.execute(
                Statement.insert_policy_structure,
                data
            )

    async def _update_policy(self, policy: Policy):
        """
        Update policy data in two iterations
        In firstly updates policy table
        then updates insurance_state table
        """
        async with self._connection.begin() as conn:
            cursor = await conn.execute(Statement.update_policy, Converter.update_policy(policy))
        policy_data = cursor.fetchone()
        if not policy_data:
            raise PolicyAlreadyUpdatedError()

        policy_state = policy.state
        setattr(policy, '__version', policy_data.version)
        await self._create_or_update_insurance_state(policy_state)
        if records := policy_state.status_history.records:
            await self._create_policy_status_records(policy_reference=policy.reference, records=records)
