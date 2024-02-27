from types import MappingProxyType

from insurance.gateway.schemas.base import PeriodType
from insurance.gateway.schemas.offer import OfferInsurer
from insurance.insurance_offer_sdk import OfferGatewayClient

from insurance.domains.policy.abstractions.adapters import OfferAdapterABC
from insurance.domains.policy.dto import (
    InsuranceOffer,
    PeriodTypeEnum,
    Period,
    ProductTypeEnum,
)
from insurance.domains.policy.model import Policy
from .offer_structure_converter import OfferStructureConverter


class OfferAdapter(OfferAdapterABC):
    def __init__(self, offer_client: OfferGatewayClient):
        self._offer_client = offer_client
        self._product_map = {
            ProductTypeEnum.OSGPO_VTS: "ogpo-vts",
            ProductTypeEnum.CASCO_LIMIT: "casco-limit",
        }

    async def get_offer(self, policy: Policy) -> InsuranceOffer:
        policy_state = policy.state
        offer_period = self._get_offer_period(policy_state.period)
        offer_product_id = self._product_map[policy_state.product]
        offer_structure = OfferStructureConverter.get_structure(policy_state.product, policy_state.structure)

        offer_response = await self._offer_client.get_offer(
            insurance=policy_state.insurance,
            product_id=offer_product_id,
            period=offer_period,
            insurer=OfferInsurer(
                iin=policy_state.insurer.title
            ),
            channel_id=policy_state.channel,
            prev_global_id=policy_state.prev_global_id,
            additional_attributes=dict(policy_state.attributes),
            **offer_structure
        )

        insurance_offer = InsuranceOffer(
            premium=offer_response.full_premium,
            cost=offer_response.extra_pay,
            reward=offer_response.extra_pay_reward,
            attributes=MappingProxyType(offer_response.attributes),
            conditions=tuple(offer_response.insurance_conditions),
        )

        return insurance_offer

    @staticmethod
    def _get_offer_period(period: Period) -> PeriodType:
        if period.type == PeriodTypeEnum.YEAR and period.value == 1:
            return PeriodType.YEAR.value
        elif period.type == PeriodTypeEnum.MONTH and period.value == 6:
            return PeriodType.MONTH6.value
        else:
            raise ValueError(f'can not get offer period from type: {period.type.value}, value: {period.value}')
