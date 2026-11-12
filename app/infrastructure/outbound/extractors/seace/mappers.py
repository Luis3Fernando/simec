from typing import Any

from app.infrastructure.outbound.extractors.shared.parsing import (
    optional_text,
    parse_date,
    to_float,
    to_int,
)
from app.domain.models.seace import (
    AwardRecord,
    RnpValidity,
    SeaceProviderPresence,
    Shareholder,
    ValidityStatus,
)

Row = dict[str, Any]


def matrix_to_rows(payload: dict[str, Any] | None) -> list[Row]:
    if not payload:
        return []
    columns = [str(c["colName"]).strip().upper() for c in payload.get("metadata", [])]
    return [dict(zip(columns, row)) for row in payload.get("resultset", [])]


def to_validity(row: Row) -> RnpValidity:
    active = (optional_text(row.get("ESTADO2")) or "").upper() == "VIGENTE"
    return RnpValidity(
        chapter=optional_text(row.get("CAPITULORNP")) or "",
        status=ValidityStatus.ACTIVE if active else ValidityStatus.INACTIVE,
        start_date=parse_date(row.get("FINICIO")),
        end_date=parse_date(row.get("FFIN")),
        department=optional_text(row.get("DEPARTAMENTOOEE")),
    )


def to_shareholder(row: Row) -> Shareholder:
    return Shareholder(
        relationship_type=optional_text(row.get("TIPO")) or "",
        document_number=optional_text(row.get("NRO_DOC")) or "",
        full_name=optional_text(row.get("NOMBRE O RAZON SOCIAL")) or "",
        share_percentage=to_float(row.get("ACCIONES")),
    )


def to_award(row: Row) -> AwardRecord:
    return AwardRecord(
        fiscal_year=to_int(row.get("PERIODO")),
        modality=optional_text(row.get("MODALIDAD")),
        contracting_entity=optional_text(row.get("ENTIDAD")) or "",
        amount=to_float(row.get("MONTO")),
        processes_count=to_int(row.get("CONVOCATORIAS")),
    )


def to_presence(row: Row) -> SeaceProviderPresence | None:
    ruc = optional_text(row.get("RUCPROVEEDOR"))
    if ruc is None:
        return None
    return SeaceProviderPresence(
        ruc=ruc,
        business_name=optional_text(row.get("PROVEEDOR")) or "",
        condition=optional_text(row.get("ESTADO")),
    )
