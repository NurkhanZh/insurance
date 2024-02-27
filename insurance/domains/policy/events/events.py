from dddmisc import DDDEvent
from dddmisc.messages import fields


class BaseEvent(DDDEvent):
    reference = fields.Uuid()

    class Meta:
        domain = 'insurance-product'
        is_baseclass = True


class UpdatePolicyStatusEvent(BaseEvent):
    channel_id = fields.String()


class PolicyInInsuranceCompletedEvent(BaseEvent):
    insurance_reference = fields.String()


class PolicyCompletedEvent(BaseEvent):
    insurance_reference = fields.String()


class PolicyReissuedEvent(BaseEvent):
    insurance_reference = fields.String()


class PolicyRescindedEvent(BaseEvent):
    insurance_reference = fields.String()


class PolicyOperatorErrorEvent(BaseEvent):
    insurance_reference = fields.String()


class PolicyRestoredEvent(BaseEvent):
    insurance_reference = fields.String()


class UpdatedPolicyCallbackEvent(DDDEvent):
    class Meta:
        domain = 'insurances-callback'

    insurance_reference = fields.String()
    global_id = fields.String(nullable=True)
    event_type = fields.String(nullable=True)
    event_time = fields.Datetime()
    attributes_json = fields.String(default='{}')
    correlation_id = fields.String(nullable=True)


class PolicyAccrueRewardCreatedEvent(BaseEvent):
    insurance_reference = fields.String()


class PolicyRetentionRewardCreatedEvent(BaseEvent):
    insurance_reference = fields.String()
