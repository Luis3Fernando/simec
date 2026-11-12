from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RnpRegistration:
    chapter: str
    provider_code: str | None = None
    payment_date: date | None = None
    procedure_number: str | None = None
    status: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class RnpRecord:
    ruc: str
    business_name: str | None = None
    registrations: tuple[RnpRegistration, ...] = ()
