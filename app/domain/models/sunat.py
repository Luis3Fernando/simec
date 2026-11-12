from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class LegalRepresentative:
    document_type: str
    document_number: str
    full_name: str
    role: str
    start_date: date | None = None


@dataclass(frozen=True, slots=True)
class BranchOffice:
    code: str
    establishment_type: str
    address: str
    economic_activity: str


@dataclass(frozen=True, slots=True)
class SunatProfile:
    tax_id: str
    taxpayer_type: str | None = None
    commercial_name: str | None = None
    registration_date: date | None = None
    activity_start_date: date | None = None
    status: str | None = None
    condition: str | None = None
    tax_alert: str | None = None
    fiscal_address: str | None = None
    economic_activities: tuple[str, ...] = ()
    electronic_issuance: str | None = None
    legal_representatives: tuple[LegalRepresentative, ...] = ()
    branch_offices: tuple[BranchOffice, ...] = ()
