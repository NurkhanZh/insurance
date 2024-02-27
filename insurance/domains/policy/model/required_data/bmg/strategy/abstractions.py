import abc
import typing as t
from uuid import UUID


T = t.TypeVar('T')
LeadItemType = t.NewType('LeadItemType', t.Literal['driver', 'vehicle', 'limit'])
InsuranceNameEnumProtocol: t.TypeAlias = str
ProductTypeEnumProtocol: t.TypeAlias = str


class PolicyInsurerProtocol(t.Protocol):
    iin: str


class StructureVehicle(t.Protocol):
    registration_number: str


class StructureDriver(t.Protocol):
    iin: str
    is_privileged: bool = False


class StructureLimit(t.Protocol):
    value: int


class StructureProtocol(t.Protocol):
    item_reference: t.Optional[UUID]
    title: str
    type: LeadItemType
    attrs: t.Union[StructureDriver, StructureVehicle, StructureLimit]


class InsurerProtocol(t.Protocol):
    title: str
    is_privileged: bool
    reference: UUID


class PolicyStateProtocol(t.Protocol):
    product: ProductTypeEnumProtocol
    insurance: InsuranceNameEnumProtocol
    structure: t.List[StructureProtocol]
    insurer: InsurerProtocol


class PolicyProtocol(t.Protocol[T]):

    @property
    def state(self) -> PolicyStateProtocol: return ...


class ValidatePhoneResponseProtocol(t.Protocol):
    is_verified: bool


class DriverProtocol(t.Protocol):
    reference: UUID
    iin: str
    is_valid_bmg_phone: bool


class PersonResponseProtocol(t.Protocol):
    drivers: t.Sequence[DriverProtocol]


class GetVehicleResponseProtocol(t.Protocol):
    registration_number: str
    region_id: int


class ClientResponseProtocol(t.Protocol):
    iin: str


class RequiredPhone(t.TypedDict):
    required: bool
    allow_bmg: bool
    allow_otp: bool


class CheckVerifiedPhoneFunc(t.Protocol):
    def __call__(self, iin: str, insurance: str) -> t.Awaitable[ValidatePhoneResponseProtocol]:
        """Check iin and phone by BMG"""


class GetPersonsDataFunc(t.Protocol):
    def __call__(self, iin_list: t.Sequence[str]) -> t.Awaitable[PersonResponseProtocol]:
        """Get persons details as list"""


class GetVehicleFunc(t.Protocol):
    def __call__(self, registration_number: str) -> t.Awaitable[GetVehicleResponseProtocol]:
        """Get vehicle by reg_number"""


class GetClientFunc(t.Protocol):
    def __call__(self, iin: t.Optional[str], reference: t.Optional[UUID] = None) -> t.Awaitable[ClientResponseProtocol]:
        """Get client details"""


class PolicyBMGStrategyABC(abc.ABC):
    @abc.abstractmethod
    async def required_check(self, policy: PolicyProtocol) -> bool:
        pass

    @abc.abstractmethod
    async def check(self, policy: PolicyProtocol) -> t.Mapping:
        pass

    @abc.abstractmethod
    async def ensure(self, policy: PolicyProtocol) -> None:
        pass
