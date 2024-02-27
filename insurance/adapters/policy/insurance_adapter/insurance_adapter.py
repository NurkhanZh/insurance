from insurances_adapter.sdk.client import InsurancesSDK
from insurances_adapter.objects.v1.exceptions.policy import ClientNotVerified
import base64

from insurance.adapters.policy.client_domain import ClientDomainAdapter
from insurance.adapters.policy.insurance_adapter.get_save_policy_payload_strategy import (
    GetSavePolicyCascoLimitPayloadStrategy,
    GetSavePolicyOgpoVtsPayloadStrategy,
)

from insurance.domains.policy.abstractions import InsuranceAdapterABC
from insurance.domains.policy.dto import (
    InsuranceInfo,
    InsuranceNameEnum,
    ProductTypeEnum,
)
from insurance.domains.policy.exceptions import SavePolicyError
from insurance.domains.policy.model import Policy
from insurance.integrations.policy.person_domain import PersonDomainSDK


class InsuranceAdapter(InsuranceAdapterABC):
    def __init__(self, insurances_sdk: InsurancesSDK, person_sdk: PersonDomainSDK):
        self._insurances_sdk = insurances_sdk
        client_adapter = ClientDomainAdapter(person_sdk, insurances_sdk)
        self._get_save_policy_payload_strategies = {
            ProductTypeEnum.OSGPO_VTS: GetSavePolicyOgpoVtsPayloadStrategy(client_adapter),
            ProductTypeEnum.CASCO_LIMIT: GetSavePolicyCascoLimitPayloadStrategy(client_adapter),
        }
        self._base64_decoders = {
            InsuranceNameEnum.EURASIA: lambda b64: base64.b64decode(b64.encode('ascii')),
            InsuranceNameEnum.BASEL: lambda b64: base64.b64decode(b64.encode()),
        }

    async def save_policy(self, policy: Policy) -> InsuranceInfo:
        policy_state = policy.state
        if not self._get_save_policy_payload_strategies.get(policy_state.product):
            raise ValueError(f'Strategy for this product is not implemented: {policy_state.product.value}')

        strategy = self._get_save_policy_payload_strategies[policy_state.product]
        payload = await strategy.get_save_policy_payload(policy)
        try:
            insurance_response = await self._insurances_sdk.v1.policy.save_policy_draft(**payload)
        except ClientNotVerified:
            raise SavePolicyError()
        insurance_info = InsuranceInfo(
            insurance_reference=insurance_response.correlation_id,
            redirect_url=str(insurance_response.redirect_url),
        )
        return insurance_info

    async def get_policy_pdf(self, insurance_reference: str, insurance: InsuranceNameEnum) -> bytes:
        if not self._base64_decoders.get(insurance):
            raise ValueError(f'Decoder for this insurance is not implemented: {insurance.value}')

        pdf_policy_response = await self._insurances_sdk.v1.policy.get_pdf_policy(insurance_reference, insurance)
        decoder = self._base64_decoders[insurance]
        pdf_policy_bytes = decoder(pdf_policy_response.data)
        return pdf_policy_bytes
