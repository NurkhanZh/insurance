from copy import copy

import attr
import typing as t
import datetime as dt
from uuid import UUID, uuid4

from pydantic import BaseModel

from .enums import PolicyStatusEnum, PaymentTypeEnum, ProductTypeEnum, DocumentType, DocumentStatus
from .value_objects import Period, StatusRecord, PrevPolicy, Structure


class StatusHistory:

    def __init__(self, *records: StatusRecord):
        self._records = set(records)

    @property
    def records(self) -> t.List[StatusRecord]:
        return sorted(tuple(record for record in self._records), key=lambda x: x.timestamp)

    def add_record(self, status: PolicyStatusEnum, timestamp: dt.datetime):
        self._records.add(StatusRecord(status=status, timestamp=timestamp))


class Insurer(BaseModel):
    title: str
    is_privileged: bool
    reference: UUID


class Document:
    _reference: UUID
    _document_type: DocumentType
    _status: DocumentStatus

    def __init__(self, reference: UUID, document_type: DocumentType, status: DocumentStatus = None):
        self._reference = reference
        self._document_type = document_type
        self._status = status or DocumentStatus.CREATED

    @property
    def reference(self) -> UUID:
        return self._reference

    @property
    def document_type(self) -> DocumentType:
        return self._document_type

    @property
    def status(self) -> DocumentStatus:
        return self._status

    @property
    def is_confirmed(self) -> bool:
        return self._status == DocumentStatus.CONFIRMED

    @property
    def is_created(self) -> bool:
        return self._status == DocumentStatus.CREATED

    @property
    def is_canceled(self) -> bool:
        return self._status == DocumentStatus.CANCELED

    def set_confirmed_status(self):
        self._status = DocumentStatus.CONFIRMED

    def set_canceled_status(self):
        self._status = DocumentStatus.CANCELED


class DocumentCollection:
    def __init__(self, documents: t.List[Document] = None):
        self._documents: t.List[Document] = documents or []

    @property
    def documents(self) -> t.List[Document]:
        return [copy(document) for document in self._documents]

    def add_document(self, document: Document):
        self._documents.append(document)

    def get_document_by_type(self, document_type: DocumentType) -> t.Optional[Document]:
        return next((document for document in self._documents
                     if document.document_type == document_type and document.status != DocumentStatus.CANCELED), None)


class InsuranceState:
    def __init__(self,
                 begin_date: dt.date,
                 email: t.Optional[str],
                 payment_type: PaymentTypeEnum,
                 status=PolicyStatusEnum.DRAFT,
                 redirect_url: t.Optional[str] = None,
                 insurance_reference: t.Optional[str] = None,
                 global_id: t.Optional[str] = None,
                 status_history: StatusHistory = None,
                 reference: UUID = None,
                 document_collection: DocumentCollection = None):
        self.reference = reference or uuid4()
        self.begin_date = begin_date
        self.email = email or ''
        self.payment_type = payment_type
        self._status = status
        self.redirect_url = redirect_url
        self.insurance_reference = insurance_reference
        self.global_id = global_id
        self.status_history = status_history or StatusHistory(StatusRecord(status=status, timestamp=dt.datetime.now()))
        self._document_collection = document_collection or DocumentCollection()

    @property
    def status(self):
        return self._status

    @property
    def document_collection(self):
        return self._document_collection

    def set_status(self, status: PolicyStatusEnum, timestamp: dt.datetime):
        self._status = status
        self.status_history.add_record(status=status, timestamp=timestamp)

    def create_accrue_reward(self, document_reference: UUID):
        if not self._document_collection.get_document_by_type(document_type=DocumentType.ACCRUE):
            document = Document(reference=document_reference, document_type=DocumentType.ACCRUE)
            self._document_collection.add_document(document)

    def get_accrue_reward_document(self) -> t.Optional[Document]:
        return self._document_collection.get_document_by_type(document_type=DocumentType.ACCRUE)

    def confirm_accrue_reward(self):
        document = self._document_collection.get_document_by_type(document_type=DocumentType.ACCRUE)
        if document and document.is_created:
            document.set_confirmed_status()

    def cancel_accrue_reward(self):
        document = self._document_collection.get_document_by_type(document_type=DocumentType.ACCRUE)
        if document and document.is_confirmed:
            document.set_canceled_status()

    def create_retention_reward(self, document_reference: UUID):
        if not self._document_collection.get_document_by_type(document_type=DocumentType.RETENTION):
            document = Document(reference=document_reference, document_type=DocumentType.RETENTION)
            self._document_collection.add_document(document)

    def get_retention_reward_document(self) -> t.Optional[Document]:
        return self._document_collection.get_document_by_type(document_type=DocumentType.RETENTION)

    def confirm_retention_reward(self):
        document = self._document_collection.get_document_by_type(document_type=DocumentType.RETENTION)
        if document and document.is_created:
            document.set_confirmed_status()

    def cancel_retention_reward(self):
        document = self._document_collection.get_document_by_type(document_type=DocumentType.RETENTION)
        if document and document.is_confirmed:
            document.set_canceled_status()


class Lead(BaseModel):
    reference: UUID
    is_freeze: bool
    phone: str
    creator_reference: UUID
    period: Period
    prev_policy: t.Optional[PrevPolicy]
    product_code: ProductTypeEnum
    channel: str
    insurer: Insurer
    structure: t.List[Structure]


@attr.s(frozen=True, auto_attribs=True)
class PolicyLead:
    reference: UUID


@attr.s(frozen=True, auto_attribs=True)
class PolicyCreator:
    reference: UUID
