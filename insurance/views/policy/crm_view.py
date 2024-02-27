import datetime as dt
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine

from insurance.database.policy.table import PolicyTable, StructureItem, PolicyInsurerTable, InsuranceStateTable
from insurance.domains.policy.dto import PolicyStatusEnum


class CRMView:

    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def get_policies(self,
                           status: PolicyStatusEnum = None,
                           reference: UUID = None,
                           insurer_iin: str = None,
                           create_date: dt.date = None,
                           channel: str = None,
                           vehicle_number: str = None,
                           page: int = 1,
                           limit: int = 10):
        pol = sa.alias(PolicyTable, 'pol')
        insurer = sa.alias(PolicyInsurerTable, 'insurer')
        structure = sa.alias(StructureItem, 'structure')
        insurance_state = sa.alias(InsuranceStateTable, 'insurance_state')

        pol_temp = sa.select(
            pol.c.reference,
            insurer.c.title.label('iin')
        ).join(insurer, pol.c.reference == insurer.c.policy_reference)  # noqa
        if reference:
            pol_temp = pol_temp.where(pol.c.reference == reference)
        elif insurer_iin:
            pol_temp = pol_temp.where(insurer.c.title == insurer_iin)
        else:
            create_date = create_date or dt.date.today()
            if status:
                pol_temp = pol_temp.where(pol.c.status == status)
            if create_date:
                start_datetime = (dt.datetime.combine(create_date, dt.datetime.min.time())) - dt.timedelta(hours=6)
                end_datetime = (dt.datetime.combine(create_date, dt.datetime.max.time())) - dt.timedelta(hours=6)
                pol_temp = pol_temp.where(pol.c.created_time >= start_datetime, pol.c.created_time <= end_datetime)
            if channel:
                pol_temp = pol_temp.where(pol.c.channel == channel)
        pol_temp = pol_temp.offset((page - 1) * limit).limit(limit)
        pol_temp = pol_temp.cte('pol_temp')

        insured = sa.select(
            structure.c.policy_reference,
            sa.func.array_agg(
                structure.c.attrs['iin']
            ).label('insured')
        ).join(
            pol_temp, structure.c.policy_reference == pol_temp.c.reference  # noqa
        ).where(structure.c.type == 'driver').group_by(structure.c.policy_reference)
        vehicles = sa.select(
            structure.c.policy_reference,
            sa.func.array_agg(
                structure.c.attrs['registration_number']
            ).label('vehicles')
        ).join(
            pol_temp, structure.c.policy_reference == pol_temp.c.reference  # noqa
        ).where(structure.c.type == 'vehicle').group_by(structure.c.policy_reference)
        insured = insured.cte('insured')
        vehicles = vehicles.cte('vehicles')

        stmt = sa.select(
            pol.c.reference,
            pol.c.insurance,
            insured.c.insured,
            vehicles.c.vehicles,
            pol.c.phone,
            pol_temp.c.iin,
            pol.c.creator_reference.label('creator'),
            pol.c.cost.label('amount'),
            insurance_state.c.global_id,
            pol.c.reward,
            pol.c.created_time.label('create_time'),
            pol.c.downloaded.label('can_download'),
            sa.text("'' as insurer_title"),
            pol.c.channel,
            pol.c.status
        ).join(
            pol_temp, pol_temp.c.reference == pol.c.reference  # noqa
        ).join(
            insured, pol.c.reference == insured.c.policy_reference
        ).join(
            vehicles, pol.c.reference == vehicles.c.policy_reference
        ).join(
            insurance_state, insurance_state.c.reference == pol.c.actual_insurance_state
        )

        async with self._engine.begin() as conn:
            cursor = await conn.execute(stmt)
            policy_list = cursor.fetchall()

        return [policy._asdict() for policy in policy_list]

    async def get_count_policies(self,
                                 status: PolicyStatusEnum = None,
                                 reference: UUID = None,
                                 insurer_iin: str = None,
                                 create_date: dt.date = None,
                                 channel: str = None,
                                 vehicle_number: str = None):
        pol = sa.alias(PolicyTable, 'pol')
        insurer = sa.alias(PolicyInsurerTable, 'insurer')

        pol_temp = sa.select(
            sa.func.count(pol.c.reference)
        ).join(insurer, pol.c.reference == insurer.c.policy_reference)  # noqa
        if reference:
            pol_temp = pol_temp.where(pol.c.reference == reference)
        elif insurer_iin:
            pol_temp = pol_temp.where(insurer.c.title == insurer_iin)
        else:
            create_date = create_date or dt.date.today()
            if status:
                pol_temp = pol_temp.where(pol.c.status == status)
            if create_date:
                start_datetime = (dt.datetime.combine(create_date, dt.datetime.min.time())) - dt.timedelta(hours=6)
                end_datetime = (dt.datetime.combine(create_date, dt.datetime.max.time())) - dt.timedelta(hours=6)
                pol_temp = pol_temp.where(pol.c.created_time >= start_datetime, pol.c.created_time <= end_datetime)
            if channel:
                pol_temp = pol_temp.where(pol.c.channel == channel)
        async with self._engine.begin() as conn:
            cursor = await conn.execute(pol_temp)
            count = cursor.scalar()

        return count
