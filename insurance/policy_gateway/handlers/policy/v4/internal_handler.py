import datetime as dt
from uuid import UUID

from fastapi import Query
from fastapi.requests import Request

from insurance.policy_gateway.schemas.policy import v1
from insurance.domains.policy import commands as cmd


async def create_policy(request: Request, data: v1.CreatePolicyRequest) -> v1.CreatePolicyResponse:
    command = cmd.CreatePolicyCommand.load(
        {'lead': {'reference': data.lead.reference}, 'insurance': data.insurance.code}
    )
    policy = await request.state.messagebus.handle(command)

    return v1.CreatePolicyResponse(reference=policy.reference)


async def get_policy(request: Request, reference: UUID) -> v1.InternalPolicyResponse:
    policy = await request.state.policy_view.get_policy(reference)

    return v1.InternalPolicyResponse(**policy)


async def get_policies(request: Request,
                       page: int = 1,
                       status: str | None = None,
                       creator: str | None = None,
                       start_date: dt.date = Query(default=dt.date.today(), alias='start-date'),
                       end_date: dt.date = Query(default=dt.date.today(), alias='end-date'),
                       limit: int = Query(default=10, le=10, ge=1)
                       ) -> v1.InternalPoliciesResponse:
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

    return v1.InternalPoliciesResponse(data=policy_list, items=count, limit=limit, page=page, pages_count=page_count)
