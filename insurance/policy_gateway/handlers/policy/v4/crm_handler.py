import datetime as dt
import typing as t
from uuid import UUID

from fastapi import Query
from fastapi.requests import Request

from insurance.domains.policy import commands as cmd
from insurance.domains.policy.dto import PolicyStatusEnum
from insurance.policy_gateway.schemas.policy import v1


async def get_policy(request: Request, reference: UUID) -> v1.CRMPolicyResponse:
    policy = await request.state.policy_view.get_policy(reference)

    return v1.CRMPolicyResponse(**policy)


async def get_policies(request: Request,
                       status: t.Optional[str] = None,
                       reference: t.Optional[str] = None,
                       insurer_iin: str | None = None,
                       create_date: dt.date | None = None,
                       channel: str | None = None,
                       vehicle_number: str | None = None,
                       page: int = 1,
                       limit: int = Query(default=10, le=10, ge=1)
                       ) -> v1.CRMPoliciesResponse:
    policy_list = await request.state.crm_policy_view.get_policies(status=status,
                                                                   reference=reference,
                                                                   insurer_iin=insurer_iin,
                                                                   create_date=create_date,
                                                                   channel=channel,
                                                                   vehicle_number=vehicle_number,
                                                                   page=page,
                                                                   limit=limit)
    count = await request.state.crm_policy_view.get_count_policies(status=status,
                                                                   reference=reference,
                                                                   insurer_iin=insurer_iin,
                                                                   create_date=create_date,
                                                                   channel=channel,
                                                                   vehicle_number=vehicle_number)
    page_count = (count // limit) + 1

    return v1.CRMPoliciesResponse(data=policy_list, items=count, limit=limit, page=page, pages_count=page_count)


async def set_rescinded_policy(request: Request, reference: UUID, data: v1.SetRescindedPolicyRequest):
    insurance_reference = await request.state.policy_view.get_insurance_reference_by_global_id(data.global_id)  # noqa
    command = cmd.UpdatePolicyStatusCommand(
        insurance_reference=insurance_reference,
        global_id=data.global_id,
        event_type=PolicyStatusEnum.RESCINDED.value,
        event_time=data.timestamp,
        attributes_json=data.attributes.model_dump_json() if data.attributes else '{}'
    )
    await request.state.messagebus.handle(command)


async def set_reissued_policy(request: Request, reference: UUID, data: v1.SetReissuedPolicyRequest):
    insurance_reference = await request.state.policy_view.get_insurance_reference_by_global_id(data.global_id)  # noqa
    command = cmd.UpdatePolicyStatusCommand(
        insurance_reference=insurance_reference,
        global_id=data.global_id,
        event_type=PolicyStatusEnum.REISSUED.value,
        event_time=data.timestamp,
        attributes_json=data.attributes.model_dump_json() if data.attributes else '{}'
    )
    await request.state.messagebus.handle(command)


async def set_operator_error_policy(request: Request, reference: UUID, data: v1.SetOperatorErrorRequest):
    insurance_reference = await request.state.policy_view.get_insurance_reference_by_global_id(data.global_id)
    command = cmd.UpdatePolicyStatusCommand(insurance_reference=insurance_reference,
                                            global_id=data.global_id,
                                            event_type=PolicyStatusEnum.OPERATOR_ERROR.value,
                                            event_time=data.timestamp)
    await request.state.messagebus.handle(command)
