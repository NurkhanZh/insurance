from uuid import UUID

from insurances_adapter.objects.v1.exceptions import RequiredSetDriverLicense, WrongDriverLicense
from insurances_adapter.sdk.client import InsurancesSDK

from insurance.integrations.policy.person_domain import PersonDomainSDK


class ClientDomainAdapter:

    def __init__(self, client_sdk: PersonDomainSDK, insurances_sdk: InsurancesSDK):
        self._client_sdk = client_sdk
        self._insurances_sdk = insurances_sdk

    async def get_extended_person(self, reference: UUID) -> dict:
        person = await self._client_sdk.get_client(iin=None, reference=reference)
        if person.driver_license:
            driver_certificate = dict(
                number=person.driver_license.number,
                issue_date=person.driver_license.issue_date
            )
        else:
            driver_certificate = None
        try:
            response = await self._insurances_sdk.v1.person.get_person_age_experience_id(
                iin=person.iin,
                driver_certificate=driver_certificate
            )
            age_experience_id = response.age_experience_id
        except (RequiredSetDriverLicense, WrongDriverLicense):
            age_experience_id = None
        # При необходжимости сюда может быть добавлен метод get_attributes
        return person.model_dump() | dict(age_experience_id=age_experience_id)

    async def get_person(self, reference: UUID) -> dict:
        person = await self._client_sdk.get_client(iin=None, reference=reference)
        return person.model_dump()
