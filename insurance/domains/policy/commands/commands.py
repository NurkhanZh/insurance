import json

from dddmisc import DDDCommand
from dddmisc import DDDStructure
from dddmisc.messages import fields


class Lead(DDDStructure):
    reference = fields.Uuid()


class BaseCommand(DDDCommand):
    class Meta:
        domain = 'insurance-integration'
        is_baseclass = True


class CreatePolicyCommand(BaseCommand):
    lead = fields.Structure(Lead)
    insurance = fields.String()


class UpdatePolicyCommand(BaseCommand):
    reference = fields.Uuid()
    email = fields.String(nullable=True)
    begin_date = fields.Date(nullable=True)
    payment_type = fields.Integer(nullable=True)


class GetPolicyPDFCommand(BaseCommand):
    reference = fields.Uuid()


class SavePolicyToInsuranceCommand(BaseCommand):
    reference = fields.Uuid()


class CreatePolicyAccrueRewardCommand(BaseCommand):
    reference = fields.Uuid()
    insurance_reference = fields.String()


class ConfirmPolicyAccrueRewardCommand(BaseCommand):
    reference = fields.Uuid()
    insurance_reference = fields.String()


class CancelPolicyAccrueRewardCommand(BaseCommand):
    reference = fields.Uuid()
    insurance_reference = fields.String()


class DownloadPolicyPDFCommand(BaseCommand):
    reference = fields.Uuid()


class UpdatePolicyStatusCommand(BaseCommand):
    insurance_reference = fields.String()
    global_id = fields.String(nullable=True)
    event_type = fields.String(nullable=True)
    event_time = fields.Datetime()
    attributes_json = fields.String(default='{}')


class CreatePolicyRetentionRewardCommand(BaseCommand):
    reference = fields.Uuid()
    insurance_reference = fields.String()


class ConfirmPolicyRetentionRewardCommand(BaseCommand):
    reference = fields.Uuid()
    insurance_reference = fields.String()


class CancelPolicyRetentionRewardCommand(BaseCommand):
    reference = fields.Uuid()
    insurance_reference = fields.String()


class GetPolicyRequiredData(BaseCommand):
    reference = fields.Uuid()
