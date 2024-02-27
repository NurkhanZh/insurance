import datetime as dt
import typing as t
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine

from insurance.database.policy.table import (
    PolicyTable, StructureItem, PolicyInsurerTable, InsuranceStateTable, PolicyStatusRecordTable
)
from insurance.domains.policy.exceptions import PolicyNotFoundError


class View:

    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def get_policy(self, reference: UUID) -> dict:
        pol = sa.alias(PolicyTable, 'pol')
        insurer = sa.alias(PolicyInsurerTable, 'insurer')
        structure = sa.alias(StructureItem, 'structure')
        insurance_state = sa.alias(InsuranceStateTable, 'insurance_state')
        record = sa.alias(PolicyStatusRecordTable, 'record')

        structure_stmt = sa.select(
            structure.c.policy_reference,
            sa.func.json_agg(
                sa.func.jsonb_build_object(
                    'item_reference', structure.c.item_reference,
                    'type', structure.c.type,
                    'title', structure.c.title,
                    'attrs', structure.c.attrs,
                )
            ).label('structure_items')
        ).where(structure.c.policy_reference == reference).group_by(structure.c.policy_reference)

        record_stmt = sa.select(
            record.c.policy_reference,
            sa.func.json_agg(
                sa.func.jsonb_build_object(
                    'status', record.c.status,
                    'timestamp', record.c.timestamp
                )
            ).label('policy_history')
        ).where(record.c.policy_reference == reference).group_by(record.c.policy_reference)

        structure_stmt = structure_stmt.cte('structure_stmt')
        record_stmt = record_stmt.cte('record_stmt')
        stmt = sa.select(
            pol.c.reference,
            pol.c.created_time.label('created'),
            pol.c.status,
            pol.c.lead_reference.label('structure_reference'),
            sa.func.jsonb_build_object('code', pol.c.product).label('product'),
            sa.func.jsonb_build_object('code', pol.c.insurance).label('insurance'),
            sa.func.jsonb_build_object('reference', pol.c.lead_reference).label('lead'),
            pol.c.premium,
            pol.c.cost.label('coast'),
            pol.c.reward,
            pol.c.retention_reward,
            sa.case(
                (pol.c.prev_global_id.isnot(None),
                 sa.func.jsonb_build_object(
                     'global_id', pol.c.prev_global_id,
                     'description', pol.c.prev_global_id,
                     'insurance', sa.func.jsonb_build_object('code', pol.c.insurance))), else_=None
            ).label('prev_policy'),
            sa.func.jsonb_build_object(
                'is_privileged', insurer.c.is_privileged,
                'reference', insurer.c.reference,
                'title', insurer.c.title
            ).label('insurer'),
            pol.c.phone,
            structure_stmt.c.structure_items.label('structure'),
            pol.c.attributes,
            sa.func.json_build_object(
                'type', pol.c.period_type,
                'value', pol.c.period_value
            ).label('period'),
            insurance_state.c.begin_date,
            insurance_state.c.end_date,
            insurance_state.c.global_id,
            sa.text("null as address"),
            pol.c.conditions,
            insurance_state.c.email,
            insurance_state.c.redirect_url,
            pol.c.downloaded,
            record_stmt.c.policy_history,
            sa.func.json_build_object('code', pol.c.channel).label('channel'),
            sa.func.json_build_object('reference', pol.c.creator_reference).label('creator')
        ).join(
            insurer, insurer.c.policy_reference == pol.c.reference  # noqa
        ).join(
            structure_stmt, structure_stmt.c.policy_reference == pol.c.reference
        ).join(
            insurance_state, insurance_state.c.reference == pol.c.actual_insurance_state
        ).join(
            record_stmt, record_stmt.c.policy_reference == pol.c.reference, isouter=True
        ).where(pol.c.reference == reference)

        async with self._engine.begin() as conn:
            cursor = await conn.execute(stmt)
            row = cursor.first()
        if not row:
            raise PolicyNotFoundError()
        return row._asdict()

    async def get_policies(self,
                           status: t.Optional[str] = None,
                           start_date: t.Optional[dt.date] = None,
                           end_date: t.Optional[dt.date] = None,
                           creator: t.Optional[UUID] = None,
                           page: int = 1,
                           limit: int = 10, ) -> list[dict]:
        pol = sa.alias(PolicyTable, 'pol')
        insurer = sa.alias(PolicyInsurerTable, 'insurer')
        structure = sa.alias(StructureItem, 'structure')
        insurance_state = sa.alias(InsuranceStateTable, 'insurance_state')

        pol_ref = sa.select(pol.c.reference).order_by(pol.c.created_time.desc())
        if status:
            pol_ref = pol_ref.where(pol.c.status == status)
        if start_date:
            start_date = (dt.datetime.combine(start_date, dt.datetime.min.time())) - dt.timedelta(hours=6)
            pol_ref = pol_ref.where(pol.c.created_time >= start_date)
        if end_date:
            end_date = (dt.datetime.combine(end_date, dt.datetime.max.time())) - dt.timedelta(hours=6)
            pol_ref = pol_ref.where(pol.c.created_time <= end_date)
        if creator:
            pol_ref = pol_ref.where(pol.c.creator_reference == creator)

        pol_ref = pol_ref.offset((page - 1) * limit).limit(limit)

        pol_ref = pol_ref.cte('pol_ref')

        structure_stmt = sa.select(
            structure.c.policy_reference,
            sa.func.json_agg(
                sa.func.jsonb_build_object(
                    'item_reference', structure.c.item_reference,
                    'type', structure.c.type,
                    'title', structure.c.title,
                    'attrs', structure.c.attrs,
                )
            ).label('structure_items')
        ).join(pol_ref, structure.c.policy_reference == pol_ref.c.reference).group_by(structure.c.policy_reference) # noqa

        structure_stmt = structure_stmt.cte('structure_stmt')

        stmt = sa.select(
            pol.c.reference,
            insurance_state.c.begin_date,
            pol.c.cost.label('coast'),
            pol.c.lead_reference.label('structure_reference'),
            pol.c.conditions,
            sa.func.jsonb_build_object('code', pol.c.insurance).label('insurance'),
            sa.func.jsonb_build_object(
                'is_privileged', insurer.c.is_privileged,
                'reference', insurer.c.reference,
                'title', insurer.c.title
            ).label('insurer'),
            sa.func.json_build_object(
                'type', pol.c.period_type,
                'value', pol.c.period_value
            ).label('period'),
            pol.c.phone,
            pol.c.premium,
            sa.case(
                (pol.c.prev_global_id.isnot(None),
                 sa.func.jsonb_build_object(
                     'global_id', pol.c.prev_global_id,
                     'description', pol.c.prev_global_id,
                     'insurance', sa.func.jsonb_build_object('code', pol.c.insurance))), else_=None
            ).label('prev_policy'),
            sa.func.jsonb_build_object('code', pol.c.product).label('product'),
            pol.c.reward,
            pol.c.status,
            structure_stmt.c.structure_items.label('structure'),
            pol.c.created_time.label('created'),
            pol.c.downloaded,
        ).join(
            pol_ref, pol.c.reference == pol_ref.c.reference   # noqa
        ).join(
            insurer, insurer.c.policy_reference == pol.c.reference
        ).join(
            structure_stmt, structure_stmt.c.policy_reference == pol.c.reference
        ).join(
            insurance_state, insurance_state.c.reference == pol.c.actual_insurance_state
        ).order_by(pol.c.created_time.desc())

        async with self._engine.begin() as conn:
            cursor = await conn.execute(stmt)
            policy_list = cursor.fetchall()

        return [policy._asdict() for policy in policy_list]

    async def get_count(self,
                        status: t.Optional[str] = None,
                        start_date: t.Optional[dt.date] = None,
                        end_date: t.Optional[dt.date] = None,
                        creator: t.Optional[UUID] = None, ) -> int:
        pol = sa.alias(PolicyTable, 'pol')
        stmt = sa.select(sa.func.count(pol.c.reference))
        if start_date:
            start_date = (dt.datetime.combine(start_date, dt.datetime.min.time())) - dt.timedelta(hours=6)
            stmt = stmt.where(sa.cast(pol.c.created_time, sa.Date) >= start_date)
        if status:
            stmt = stmt.where(pol.c.status == status)
        if end_date:
            end_date = (dt.datetime.combine(end_date, dt.datetime.max.time())) - dt.timedelta(hours=6)
            stmt = stmt.where(sa.cast(pol.c.created_time, sa.Date) <= end_date)
        if creator:
            stmt = stmt.where(pol.c.creator_reference == creator)
        async with self._engine.begin() as conn:
            cursor = await conn.execute(stmt)
            count = cursor.scalar()

        return count

    async def get_insurance_reference_by_global_id(self, global_id: str) -> UUID:
        insurance_state = sa.alias(InsuranceStateTable, 'insurance_state')
        stmt = sa.select(insurance_state.c.insurance_reference).where(insurance_state.c.global_id == global_id)
        async with self._engine.begin() as conn:
            cursor = await conn.execute(stmt)
        ins_state = cursor.fetchone()
        if not ins_state:
            raise PolicyNotFoundError()
        return ins_state.insurance_reference
