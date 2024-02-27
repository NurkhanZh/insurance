import typing as t

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY,JSONB

from insurance.domains.policy.dto import PaymentTypeEnum, PolicyStatusEnum, DocumentStatus

SCHEMA_NAME: t.Final[str] = 'insurances_policy'

metadata = sa.MetaData(schema=SCHEMA_NAME)

PolicyStatusRecordTable = sa.Table(
    'policy_status_record', metadata,
    sa.Column('status', sa.String(50), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('policy_reference', sa.ForeignKey('policy.reference', name='status_record_policy_reference_fkey'),
              index=True, nullable=False)
)

InsuranceStateStatusRecordTable = sa.Table(
    'insurance_state_status_record', metadata,
    sa.Column('status', sa.String(50), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('insurance_state_reference',
              sa.ForeignKey('insurance_state.reference', name='status_record_insurance_state_fkey'),
              index=True, nullable=False)
)

PolicyInsurerTable = sa.Table(
    'insurer', metadata,
    sa.Column('reference', UUID(as_uuid=True), comment='Рефернс страхователя', index=True),
    sa.Column('policy_reference', sa.ForeignKey('policy.reference', name='insurer_policy_reference_fkey'),
              index=True, nullable=False),
    sa.Column('is_privileged', sa.Boolean(), comment='Признак на наличие привилегии у страхователя', nullable=False,
              default=False),
    sa.Column('title', sa.String(100), comment='Наименование', index=True)
)

StructureItem = sa.Table(
    'structure_item', metadata,
    sa.Column('item_reference', UUID(as_uuid=True), index=True, nullable=True),
    sa.Column('policy_reference', sa.ForeignKey('policy.reference', name='structure_item_policy_reference_fkey'),
              nullable=False, index=True),
    sa.Column('type', sa.String(50), comment='Тип структуры', nullable=False),
    sa.Column('title', sa.String(100), comment='Отображаемое название сущности', nullable=False),
    sa.Column('attrs', JSONB(), comment='Доп аттрибуты', nullable=False),
)


InsuranceStateTable = sa.Table(
    'insurance_state', metadata,
    sa.Column('reference', UUID(as_uuid=True), index=True, unique=True),
    sa.Column('policy_reference', sa.ForeignKey('policy.reference', name='insurance_state_policy_reference_fkey'),
              nullable=False, index=True),
    sa.Column('begin_date', sa.Date(), comment='Дата начала', nullable=False, ),
    sa.Column('end_date', sa.Date(), comment='Дата окончания', nullable=False, ),
    sa.Column('email', sa.String(100), comment='Email', nullable=True),
    sa.Column('payment_type', sa.SmallInteger(), nullable=False, default=PaymentTypeEnum.ONLY_ANY_PAY.value),
    sa.Column('redirect_url', sa.Text(), comment='Урл перехода', nullable=True, ),
    sa.Column('insurance_reference', sa.String(36), unique=True, comment='ID полиса в системе СК', nullable=True, ),
    sa.Column('global_id', sa.String(50), comment='Global ID полиса', unique=True, nullable=True),
    sa.Column('status', sa.String(50), comment='Статус полиса', nullable=False, default=PolicyStatusEnum.DRAFT.value),
    sa.UniqueConstraint('global_id', name='insurance_state_global_id_ux')
)

FinDocument = sa.Table(
    'fin_document', metadata,
    sa.Column('reference', UUID(as_uuid=True), nullable=False, unique=True),
    sa.Column('insurance_state_reference',
              sa.ForeignKey('insurance_state.reference', name='fin_document_insurance_state_reference_fkey'),
              nullable=False, index=True),
    sa.Column('type', sa.String(20), comment='Тип документа', nullable=False),
    sa.Column('status', sa.String(20), comment='Статус документа', nullable=False, default=DocumentStatus.CREATED.value)
)

PolicyTable = sa.Table(
    'policy', metadata,
    sa.Column('reference', UUID(as_uuid=True), primary_key=True, comment='Рефернс полиса'),
    sa.Column('product', sa.String(20), comment='Продукт полиса', nullable=False),
    sa.Column('insurance', sa.String(20), comment='Наименование СК', nullable=False),
    sa.Column('channel', sa.String(20), comment='Канал продаж', nullable=False),
    sa.Column('phone', sa.String(20), comment='Номер телефона страхователя', nullable=False),
    sa.Column('prev_global_id', sa.String(20), comment='Global ID предыдущего полиса', nullable=True),
    sa.Column('downloaded', sa.Boolean(), comment='Признак того что файл полиса скачен', default=False),
    sa.Column('premium', sa.Integer(), comment='Премия полиса', nullable=False),
    sa.Column('cost', sa.Integer(), comment='Стоимость полиса', nullable=False),
    sa.Column('reward', sa.DECIMAL(), comment='АВ на полиса', nullable=False),
    sa.Column('retention_reward', sa.DECIMAL(), comment='Сумма на удержание вознаграждения', nullable=True),
    sa.Column('conditions', ARRAY(sa.TEXT()), comment='Список ключей условий страхования', nullable=True),
    sa.Column('status', sa.String(50), comment='Статус полиса', nullable=False, index=True),
    sa.Column('attributes', JSONB(), comment='Параметры определения премии', nullable=False),
    sa.Column('lead_reference', UUID(as_uuid=True), comment='Референс лида', nullable=False, index=True),
    sa.Column('creator_reference', UUID(as_uuid=True), comment='Референс создателя полиса', nullable=False, index=True),
    sa.Column('period_type', sa.String(20), comment='Тип периода полиса', nullable=False),
    sa.Column('period_value', sa.SmallInteger(), comment='Значение периода', nullable=False),
    sa.Column('actual_insurance_state', UUID(as_uuid=True), comment='Референс на актуального состояние полиса',
              nullable=False),
    sa.Column('created_time', sa.DateTime(), comment='Время создание полиса', nullable=False, index=True),
    sa.Column('updated_time', sa.DateTime(), comment='Время обновления полиса', nullable=False),
    sa.Column('version', sa.SmallInteger(), comment='Версия полиса', nullable=False)
)
