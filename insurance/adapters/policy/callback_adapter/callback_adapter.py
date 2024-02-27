import json
import datetime as dt
import typing as t
from types import MappingProxyType

from insurance.domains.policy.abstractions import CallbackAdapterABC
from insurance.domains.policy.dto import StatusInfo, PolicyStatusEnum


class CallbackAdapter(CallbackAdapterABC):
    def get_status_info(self,
                        insurance_reference: str,
                        global_id: t.Optional[str],
                        event_type: str,
                        event_time: dt.datetime,
                        attributes_json: str) -> StatusInfo:
        attrs_dict = MappingProxyType(json.loads(attributes_json))
        status = None
        if event_type == 'COMPLETED':
            status = PolicyStatusEnum.COMPLETED_IN_INSURANCE
        elif event_type == 'PAYED':
            status = PolicyStatusEnum.PAYED
        elif event_type == 'REISSUED':
            status = PolicyStatusEnum.REISSUED
        elif event_type == 'RESCINDED':
            status = PolicyStatusEnum.RESCINDED
        elif event_type == 'OPERATOR_ERROR':
            status = PolicyStatusEnum.OPERATOR_ERROR
        elif event_type == 'RESTORED':
            status = PolicyStatusEnum.RESTORED
        event_time = event_time.replace(tzinfo=None)
        return StatusInfo(status_type=status, timestamp=event_time, insurance_reference=insurance_reference,
                          global_id=global_id, extra_attrs=attrs_dict)
