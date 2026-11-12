from dataclasses import dataclass
from datetime import date
from enum import Enum


class ValidityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True, slots=True)
class RnpValidity:
    chapter: str
    status: ValidityStatus
    start_date: date | None
    end_date: date | None
    department: str | None


@dataclass(frozen=True, slots=True)
class Shareholder:
    relationship_type: str
    document_number: str
    full_name: str
    share_percentage: float


@dataclass(frozen=True, slots=True)
class AwardRecord:
    fiscal_year: int
    modality: str | None
    contracting_entity: str
    amount: float
    processes_count: int


@dataclass(frozen=True, slots=True)
class SeaceProviderPresence:
    ruc: str
    business_name: str
    condition: str | None = None


@dataclass(frozen=True, slots=True)
class SeaceProviderRecord:
    ruc: str
    validities: tuple[RnpValidity, ...] = ()
    shareholders: tuple[Shareholder, ...] = ()
    awards: tuple[AwardRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class SeaceLinkedProvider:
    presence: SeaceProviderPresence
    record: SeaceProviderRecord


@dataclass(frozen=True, slots=True)
class SeacePersonRecord:
    document_number: str
    linked_providers: tuple[SeaceLinkedProvider, ...] = ()
