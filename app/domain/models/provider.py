from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class ValidityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    NO_DATA = "NO_DATA"


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
class AuditResult:
    source_name: str
    query_parameter: str
    duration_ms: int
    status: AuditStatus
    details: str | None
    executed_at_utc: datetime


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    tax_id: str
    validities: tuple[RnpValidity, ...] = ()
    shareholders: tuple[Shareholder, ...] = ()
    awards: tuple[AwardRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class ProviderReport:
    profile: ProviderProfile
    audit_entries: tuple[AuditResult, ...] = ()
