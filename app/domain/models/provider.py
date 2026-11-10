from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


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
class TaxpayerDetails:
    document_type: str
    document_number: str
    legal_name: str
    tax_status: str | None = None
    tax_condition: str | None = None
    fiscal_address: str | None = None
    ubigeo: str | None = None
    department: str | None = None
    province: str | None = None
    district: str | None = None
    first_surname: str | None = None
    second_surname: str | None = None
    given_names: str | None = None


@dataclass(frozen=True, slots=True)
class SunatProfile:
    tax_id: str
    taxpayer_type: str | None = None
    commercial_name: str | None = None
    registration_date: str | None = None
    activity_start_date: str | None = None
    status: str | None = None
    condition: str | None = None
    fiscal_address: str | None = None
    economic_activities: list[str] = field(default_factory=list)
    electronic_issuance: str | None = None
    legal_representatives: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    tax_id: str
    validities: tuple[RnpValidity, ...] = ()
    shareholders: tuple[Shareholder, ...] = ()
    awards: tuple[AwardRecord, ...] = ()
    taxpayer_details: TaxpayerDetails | None = None
    sunat_profile: SunatProfile | None = None


@dataclass(frozen=True, slots=True)
class ProviderReport:
    profile: ProviderProfile
    audit_entries: tuple[AuditResult, ...] = ()
