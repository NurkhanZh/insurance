import asyncio
from typing import Dict, List

from insurance.adapters.policy.client_domain import ClientDomainAdapter
from insurance.adapters.policy.insurance_adapter.get_save_policy_payload_strategy import GetSavePolicyPayloadStrategyABC
from insurance.domains.policy.dto import Structure, Insurer
from insurance.domains.policy.model import Policy


class GetSavePolicyCascoLimitPayloadStrategy(GetSavePolicyPayloadStrategyABC):
    product = 'casco-limit'

    def __init__(self, client_adapter: ClientDomainAdapter):
        self._client_adapter = client_adapter

    async def get_save_policy_payload(self, policy: Policy) -> Dict:
        policy_state = policy.state
        structure = self._get_structure(policy_state.structure)
        driver_tasks = asyncio.gather(*[self._extend_driver(driver) for driver in structure['drivers']])
        insurer_task = self._extend_insurer(policy_state.insurer)
        drivers, insurer = await asyncio.gather(driver_tasks, insurer_task)

        return dict(
            product_id=self.product,
            draft_reference=policy_state.actual_insurance_state.reference,
            insurer=insurer,
            structure={
                'drivers': drivers,
                'vehicle': structure['vehicle'],
                'limit': structure['limit'],
            },
            phone=policy_state.phone,
            start_date=policy_state.begin_date.strftime('%Y-%m-%d'),
            period={'type': policy_state.period.type.value, 'value': policy_state.period.value},
            payment_type='any',
            email=policy_state.email or None,
            prev_global_id=policy_state.prev_global_id,
            insurance=policy_state.insurance.value,
        )

    @staticmethod
    def _get_structure(structures: List[Structure]) -> Dict:
        result_structure = {
            'drivers': [],
            'vehicle': None,
            'limit': 0,
        }
        for structure in structures:
            if structure.type == 'driver':
                result_structure['drivers'].append(
                    {'reference': structure.item_reference, 'is_privileged': structure.attrs.is_privileged}
                )

            elif structure.type == 'vehicle':
                result_structure['vehicle'] = {'registration_number': structure.attrs.registration_number}

            elif structure.type == 'limit':
                result_structure['limit'] = structure.attrs.value

        return result_structure

    async def _extend_driver(self, driver: dict) -> dict:
        person = await self._client_adapter.get_extended_person(driver['reference'])
        return dict(
            iin=person['iin'],
            age_experience_id=person['age_experience_id'],
            is_privileged=driver['is_privileged'],
            driver_certificate=person['driver_license'],
            phone=person.get('phone'),
        )

    async def _extend_insurer(self, insurer: Insurer) -> dict:
        person = await self._client_adapter.get_person(reference=insurer.reference)
        return dict(
            iin=person['iin'],
            is_privileged=insurer.is_privileged,
        )
