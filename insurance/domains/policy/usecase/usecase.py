from uuid import UUID
import asyncio

from dddmisc import AbstractAsyncUnitOfWork, AsyncMessageBus
from tenacity import retry, retry_if_exception_type

from insurance.domains.policy.abstractions import (
    LeadAdapterABC, OfferAdapterABC, RedLockClientABC, InsuranceAdapterABC, FinDocumentAdapterABC, S3AdapterABC,
    CallbackAdapterABC, PolicyRequiredDataFacadeABC
)
from insurance.domains.policy.commands import (
    CreatePolicyCommand, UpdatePolicyCommand, SavePolicyToInsuranceCommand, CreatePolicyAccrueRewardCommand,
    DownloadPolicyPDFCommand, GetPolicyPDFCommand, ConfirmPolicyAccrueRewardCommand, CancelPolicyAccrueRewardCommand,
    CreatePolicyRetentionRewardCommand, UpdatePolicyStatusCommand, ConfirmPolicyRetentionRewardCommand,
    CancelPolicyRetentionRewardCommand, GetPolicyRequiredData
)
from insurance.domains.policy.events import (
    PolicyInInsuranceCompletedEvent, PolicyRestoredEvent, PolicyReissuedEvent, PolicyRescindedEvent,
    PolicyOperatorErrorEvent, PolicyCompletedEvent, UpdatedPolicyCallbackEvent, PolicyAccrueRewardCreatedEvent,
    PolicyRetentionRewardCreatedEvent
)
from insurance.domains.policy.model import Policy
from insurance.domains.policy.dto import InsuranceNameEnum, PolicyStatusEnum
from insurance.domains.policy.exceptions import PolicyAlreadyUpdatedError


class PolicyUseCases:
    def __init__(self,
                 messagebus: AsyncMessageBus,
                 redlock_client: RedLockClientABC,
                 lead_adapter: LeadAdapterABC,
                 offer_adapter: OfferAdapterABC,
                 insurance_adapter: InsuranceAdapterABC,
                 fin_doc_adapter: FinDocumentAdapterABC,
                 s3_adapter: S3AdapterABC,
                 callback_adapter: CallbackAdapterABC,
                 required_data_facade: PolicyRequiredDataFacadeABC):
        self._messagebus = messagebus
        self._redlock = redlock_client
        self._lead_adapter = lead_adapter
        self._offer_adapter = offer_adapter
        self._insurance_adapter = insurance_adapter
        self._fin_doc_adapter = fin_doc_adapter
        self._s3_adapter = s3_adapter
        self._callback_adapter = callback_adapter
        self._required_data_facade = required_data_facade

    async def create_policy(self, command: CreatePolicyCommand, uow: AbstractAsyncUnitOfWork):
        insurance = InsuranceNameEnum(command.insurance)
        lead, offer = await asyncio.gather(
            self._lead_adapter.get_lead(lead_reference=command.lead.reference),
            self._lead_adapter.get_offer(insurance=insurance, lead_reference=command.lead.reference)
        )
        policy = Policy.create(lead=lead, offer=offer, insurance=insurance)
        async with uow:
            uow.repository.add(policy)
            await uow.commit()
        return policy

    @retry(retry=retry_if_exception_type(PolicyAlreadyUpdatedError))
    async def update_policy(self, command: UpdatePolicyCommand, uow: AbstractAsyncUnitOfWork):  # noqa
        async with uow:
            policy: Policy = await uow.repository.get(command.reference)
            policy.update_policy(begin_date=command.begin_date,
                                 email=command.email,
                                 payment_type=command.payment_type)
            await uow.commit()
        return policy

    @retry(retry=retry_if_exception_type(PolicyAlreadyUpdatedError))
    async def save_policy(self, command: SavePolicyToInsuranceCommand, uow: AbstractAsyncUnitOfWork):
        async with (await self._redlock.lock(f'policy-save: {command.reference}')):
            async with uow:
                policy: Policy = await uow.repository.get(command.reference)
                if policy.state.insurance_reference:
                    return policy
                await self._required_data_facade.ensure_verified(policy)
                insurance_info = await self._insurance_adapter.save_policy(policy)
                policy.set_insurance_info(insurance_reference=insurance_info.insurance_reference,
                                          redirect_url=insurance_info.redirect_url)
                await uow.commit()
        return policy

    @retry(retry=retry_if_exception_type(PolicyAlreadyUpdatedError))
    async def update_insurance_offer(self, event: PolicyInInsuranceCompletedEvent, uow: AbstractAsyncUnitOfWork):
        async with uow:
            policy: Policy = await uow.repository.get(event.reference)
            offer = await self._offer_adapter.get_offer(policy)
            policy.update_offer(offer=offer, insurance_reference=event.insurance_reference)
            await uow.commit()

    async def handle_update_policy_status_event(self, event: UpdatedPolicyCallbackEvent, uow: AbstractAsyncUnitOfWork):
        await self._messagebus.handle(UpdatePolicyStatusCommand(insurance_reference=event.insurance_reference,
                                                                global_id=event.global_id,
                                                                event_type=event.event_type,
                                                                event_time=event.event_time,
                                                                attributes_json=event.attributes_json))

    @retry(retry=retry_if_exception_type(PolicyAlreadyUpdatedError))
    async def update_policy_status(self, command: UpdatePolicyStatusCommand, uow: AbstractAsyncUnitOfWork):
        async with uow:
            status_info = self._callback_adapter.get_status_info(insurance_reference=command.insurance_reference,
                                                                 global_id=command.global_id,
                                                                 event_type=command.event_type,
                                                                 event_time=command.event_time,
                                                                 attributes_json=command.attributes_json)
            policy_ref: UUID = await uow.repository.get_reference_by_insurance_reference(command.insurance_reference)
            policy: Policy = await uow.repository.get(policy_ref)
            policy.update_status(status_info=status_info)
            await uow.commit()
        return policy

    async def create_policy_accrue_reward(self, command: CreatePolicyAccrueRewardCommand, uow: AbstractAsyncUnitOfWork):
        async with (await self._redlock.lock(f'policy-create-accrue-reward: {command.reference}')):
            async with uow:
                policy: Policy = await uow.repository.get(command.reference)
                if not policy.accrue_reward_document:
                    document_reference = await self._fin_doc_adapter.create_pay_reward(policy=policy)
                    policy.create_accrue_reward(insurance_reference=command.insurance_reference,
                                                document_reference=document_reference)
                    await uow.commit()
        return policy

    async def confirm_policy_accrue_reward(self, command: ConfirmPolicyAccrueRewardCommand, uow: AbstractAsyncUnitOfWork):
        async with uow:
            policy: Policy = await uow.repository.get(command.reference)
            document = policy.accrue_reward_document
            if document and document.is_created:
                await self._fin_doc_adapter.confirm_pay_reward(policy_reference=policy.reference,
                                                               insurance=policy.state.insurance)
                policy.confirm_accrue_reward(insurance_reference=command.insurance_reference)
                await uow.commit()
        return policy

    async def cancel_policy_accrue_reward(self, command: CancelPolicyAccrueRewardCommand, uow: AbstractAsyncUnitOfWork):
        async with (await self._redlock.lock(f'policy-cancel-accrue-reward: {command.reference}')):
            async with uow:
                policy: Policy = await uow.repository.get(command.reference)
                document = policy.accrue_reward_document
                if document and document.is_confirmed:
                    await self._fin_doc_adapter.cancel_reward(policy_reference=policy.reference,
                                                              insurance=policy.state.insurance)
                    policy.cancel_accrue_reward(insurance_reference=command.insurance_reference)
                    await uow.commit()
        return policy

    async def create_policy_retention_reward(self, command: CreatePolicyRetentionRewardCommand, uow: AbstractAsyncUnitOfWork):
        async with (await self._redlock.lock(f'policy-create-retention-reward: {command.reference}')):
            async with uow:
                policy: Policy = await uow.repository.get(command.reference)
                if not policy.retention_reward_document:
                    document_reference = await self._fin_doc_adapter.create_retention_reward(policy)
                    policy.create_retention_reward(insurance_reference=command.insurance_reference,
                                                   document_reference=document_reference)
                    await uow.commit()
        return policy

    async def confirm_policy_retention_reward(self, command: ConfirmPolicyRetentionRewardCommand, uow: AbstractAsyncUnitOfWork):
        async with uow:
            policy: Policy = await uow.repository.get(command.reference)
            document = policy.retention_reward_document
            if document and document.is_created:
                await self._fin_doc_adapter.confirm_retention_reward(policy_reference=policy.reference,
                                                                     insurance=policy.state.insurance)
                policy.confirm_retention_reward(insurance_reference=command.insurance_reference)
                await uow.commit()
        return policy

    async def cancel_policy_retention_reward(self, command: CancelPolicyRetentionRewardCommand, uow: AbstractAsyncUnitOfWork):
        async with (await self._redlock.lock(f'policy-cancel-retention-reward: {command.reference}')):
            async with uow:
                policy: Policy = await uow.repository.get(command.reference)
                document = policy.retention_reward_document
                if document and document.is_confirmed:
                    await self._fin_doc_adapter.cancel_reward(policy_reference=policy.reference,
                                                              insurance=policy.state.insurance)
                    policy.cancel_retention_reward(insurance_reference=command.insurance_reference)
                    await uow.commit()
        return policy

    @retry(retry=retry_if_exception_type(PolicyAlreadyUpdatedError))
    async def download_policy_pdf(self, command: DownloadPolicyPDFCommand, uow: AbstractAsyncUnitOfWork):
        async with (await self._redlock.lock(f'policy-download: {command.reference}')):
            async with uow:
                policy: Policy = await uow.repository.get(command.reference)
                policy_state = policy.state
                if policy_state.downloaded:
                    return policy_state.downloaded

                pdf_byte = await self._insurance_adapter.get_policy_pdf(
                    insurance_reference=policy_state.insurance_reference, insurance=policy_state.insurance
                )
                await self._s3_adapter.upload_policy_file(data=pdf_byte, policy_reference=policy.reference)
                policy.set_pdf_downloaded()
                await uow.commit()
        return policy.state.downloaded

    async def get_policy_pdf(self, command: GetPolicyPDFCommand, uow: AbstractAsyncUnitOfWork):
        async with uow:
            policy: Policy = await uow.repository.get(command.reference)
            policy_state = policy.state
            if policy_state.downloaded:
                return self._s3_adapter.get_url(policy.reference)

            if policy_state.status == PolicyStatusEnum.COMPLETED:
                await self._messagebus.handle(DownloadPolicyPDFCommand(reference=policy.reference))
                return self._s3_adapter.get_url(policy.reference)

    async def get_required_data(self, command: GetPolicyRequiredData, uow: AbstractAsyncUnitOfWork):
        async with uow:
            policy = await uow.repository.get(command.reference)

        return await self._required_data_facade.check(policy)

    async def handle_policy_completed_event(self, event: PolicyCompletedEvent, uow: AbstractAsyncUnitOfWork):
        await asyncio.gather(
            self._messagebus.handle(CreatePolicyAccrueRewardCommand(reference=event.reference,
                                                                    insurance_reference=event.insurance_reference)),
            self._messagebus.handle(DownloadPolicyPDFCommand(reference=event.reference))
        )

    async def handle_policy_accrue_reward_created_event(self, event: PolicyAccrueRewardCreatedEvent,
                                                        uow: AbstractAsyncUnitOfWork):
        await self._messagebus.handle(ConfirmPolicyAccrueRewardCommand(reference=event.reference,
                                                                       insurance_reference=event.insurance_reference))

    async def handle_policy_retention_reward_created_event(self, event: PolicyRetentionRewardCreatedEvent,
                                                           uow: AbstractAsyncUnitOfWork):
        await self._messagebus.handle(ConfirmPolicyRetentionRewardCommand(reference=event.reference,
                                                                         insurance_reference=event.insurance_reference))

    async def handle_policy_operator_error_event(self, event: PolicyOperatorErrorEvent, uow: AbstractAsyncUnitOfWork):
        await self._messagebus.handle(
            CancelPolicyAccrueRewardCommand(reference=event.reference, insurance_reference=event.insurance_reference)
        )

    async def handle_policy_rescinded_event(self, event: PolicyRescindedEvent, uow: AbstractAsyncUnitOfWork):
        await self._messagebus.handle(
            CreatePolicyRetentionRewardCommand(reference=event.reference, insurance_reference=event.insurance_reference)
        )

    async def handle_policy_reissued_event(self, event: PolicyReissuedEvent, uow: AbstractAsyncUnitOfWork):
        await self._messagebus.handle(
            CreatePolicyRetentionRewardCommand(reference=event.reference, insurance_reference=event.insurance_reference)
        )

    async def handle_policy_restored_event(self, event: PolicyRestoredEvent, uow: AbstractAsyncUnitOfWork):
        await self._messagebus.handle(
            CancelPolicyRetentionRewardCommand(reference=event.reference, insurance_reference=event.insurance_reference)
        )
