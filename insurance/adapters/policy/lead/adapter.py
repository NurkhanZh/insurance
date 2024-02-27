from types import MappingProxyType
from uuid import UUID

from insurance.insurance_lead_sdk import LeadGatewaySDK, exc as lead_exc

from insurance.domains.policy.abstractions import LeadAdapterABC
from insurance.domains.policy.exceptions import exceptions as exc
from insurance.domains.policy.dto import (
    Lead, InsuranceNameEnum, InsuranceOffer, Structure, ProductTypeEnum, Insurer, PrevPolicy
)


class LeadAdapter(LeadAdapterABC):

    def __init__(self, lead_sdk: LeadGatewaySDK):
        self._lead_sdk = lead_sdk

    async def get_offer(self, insurance: InsuranceNameEnum, lead_reference: UUID) -> InsuranceOffer:
        try:
            response = await self._lead_sdk.get_offer(reference=lead_reference, insurance=insurance.value)
        except lead_exc.LeadNotFound:
            raise exc.LeadNotFoundError()
        except lead_exc.BaseError:
            raise exc.LeadGetOfferError()

        return InsuranceOffer(
            premium=response.premium,
            cost=response.cost,
            reward=response.reward,
            conditions=tuple([condition.code for condition in response.conditions]) if response.conditions else tuple(),
            attributes=MappingProxyType(response.attributes)
        )

    async def get_lead(self, lead_reference: UUID) -> Lead:
        try:
            response = await self._lead_sdk.get_lead(reference=lead_reference)
        except lead_exc.LeadNotFound:
            raise exc.LeadNotFoundError()

        data = response
        prev_policy = None
        insurer = data.insurer
        if data.prev_policy is not None:
            prev_policy = PrevPolicy(prev_global_id=data.prev_policy.global_id,
                                     insurance=InsuranceNameEnum(data.prev_policy.insurance.code))
        return Lead(
            reference=data.reference,
            is_freeze=data.is_freeze,
            phone=data.phone,
            creator_reference=data.creator.reference,
            period=data.period.model_dump(),
            prev_policy=prev_policy,
            product_code=ProductTypeEnum(data.product.code),
            channel=data.channel.code,
            insurer=Insurer(title=insurer.title, is_privileged=insurer.is_privileged, reference=insurer.reference),
            structure=[
                Structure(
                    item_reference=item.item_reference,
                    title=item.title,
                    type=item.type,
                    attrs=item.attrs.model_dump()
                ) for item in data.structure
            ]
        )
