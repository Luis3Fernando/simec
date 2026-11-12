from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PersonProfile:
    document_number: str
    full_name: str
    given_names: str | None = None
    first_surname: str | None = None
    second_surname: str | None = None
    check_digit: str | None = None


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    document_number: str
    legal_name: str
    status: str | None = None
    condition: str | None = None
    address: str | None = None
    ubigeo: str | None = None
    department: str | None = None
    province: str | None = None
    district: str | None = None
    via_type: str | None = None
    via_name: str | None = None
    zone_type: str | None = None
    zone_code: str | None = None
    number: str | None = None
    lot: str | None = None
    apartment: str | None = None
    block: str | None = None
    kilometer: str | None = None
