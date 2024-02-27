import datetime as dt
from uuid import UUID

from fastapi import Query
from fastapi.requests import Request
from insurance.gateway.schemas.base import ResponseModel

from insurance.domains.policy import commands as cmd
from insurance.policy_gateway.schemas.policy import v1


async def get_policy(request: Request, reference: UUID) -> v1.PublicPolicyResponse:
    policy = await request.state.policy_view.get_policy(reference)

    return v1.PublicPolicyResponse(**policy)


async def get_policies(request: Request,
                       page: int = 1,
                       status: str | None = None,
                       creator: str | None = None,
                       start_date: dt.date = Query(default=dt.date.today(), alias='start-date'),
                       end_date: dt.date = Query(default=dt.date.today(), alias='end-date'),
                       limit: int = Query(default=10, le=10, ge=1)
                       ) -> v1.PublicPoliciesResponse:
    policy_list = await request.state.policy_view.get_policies(status=status,
                                                               start_date=start_date,
                                                               end_date=end_date,
                                                               creator=creator,
                                                               page=page,
                                                               limit=limit)
    count = await request.state.policy_view.get_count(status=status,
                                                      start_date=start_date,
                                                      end_date=end_date,
                                                      creator=creator)
    page_count = (count // limit) + 1

    return v1.PublicPoliciesResponse(data=policy_list, items=count, limit=limit, page=page, pages_count=page_count)


async def update_policy(request: Request, reference: UUID, data: v1.UpdatePolicyRequest):
    command = cmd.UpdatePolicyCommand(reference=reference,
                                      email=data.email,
                                      begin_date=data.begin_date,
                                      payment_type=None)
    await request.state.messagebus.handle(command)


async def save_to_insurance(request: Request, reference: UUID):
    command = cmd.SavePolicyToInsuranceCommand(reference=reference)
    await request.state.messagebus.handle(command)


async def get_policy_pdf(request: Request, reference: UUID) -> v1.PolicyPDFResponse:
    command = cmd.GetPolicyPDFCommand(reference=reference)
    pdf_url = await request.state.messagebus.handle(command)
    return v1.PolicyPDFResponse(url=pdf_url)


async def get_required_data(request: Request, reference: UUID) -> ResponseModel:
    command = cmd.GetPolicyRequiredData(reference=reference)
    result = await request.state.messagebus.handle(command)
    return ResponseModel(data=result.model_dump())
