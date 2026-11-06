import asyncio
import time
from datetime import date, datetime, timezone
from typing import Any, Final

import httpx

from app.domain.models.provider import (
    AuditResult,
    AuditStatus,
    AwardRecord,
    ProviderProfile,
    RnpValidity,
    Shareholder,
    ValidityStatus,
)
from app.domain.ports.outbound.extractor_port import ExtractorPort

CDA_URL: Final = "https://bi.seace.gob.pe/pentaho/plugin/cda/api/doQuery?userid=public&password=key"
CDA_PATH: Final = "/public/ANTECEDENTES_PROVEEDORES/ANTECEDENTES_PROVEEDORES.cda"
TIMEOUT_S: Final = 25.0
HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://bi.seace.gob.pe",
    "Referer": (
        "https://bi.seace.gob.pe/pentaho/api/repos/:public:ANTECEDENTES_PROVEEDORES:"
        "ANTECEDENTES_PROVEEDORES.wcdf/generatedContent?userid=public&password=key"
    ),
}
QUERIES: Final = {
    "shareholders": "QUERY_R_F2_new",
    "validities": "QUERY_R_F3",
    "awards": "QUERY_R_F5_D_DASH_PROV_RESUMEN",
}

Row = dict[str, Any]


def matrix_to_rows(payload: dict[str, Any] | None) -> list[Row]:
    if not payload:
        return []
    columns = [str(c["colName"]).strip().upper() for c in payload.get("metadata", [])]
    return [dict(zip(columns, row)) for row in payload.get("resultset", [])]


def _text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _number(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def _integer(value: Any) -> int:
    return int(_number(value))


def _date(value: Any) -> date | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return datetime.strptime(text[:10], "%d/%m/%Y").date()
    except ValueError:
        return None


def _validity(row: Row) -> RnpValidity:
    active = (_text(row.get("ESTADO2")) or "").upper() == "VIGENTE"
    return RnpValidity(
        chapter=_text(row.get("CAPITULORNP")) or "",
        status=ValidityStatus.ACTIVE if active else ValidityStatus.INACTIVE,
        start_date=_date(row.get("FINICIO")),
        end_date=_date(row.get("FFIN")),
        department=_text(row.get("DEPARTAMENTOOEE")),
    )


def _shareholder(row: Row) -> Shareholder:
    return Shareholder(
        relationship_type=_text(row.get("TIPO")) or "",
        document_number=_text(row.get("NRO_DOC")) or "",
        full_name=_text(row.get("NOMBRE O RAZON SOCIAL")) or "",
        share_percentage=_number(row.get("ACCIONES")),
    )


def _award(row: Row) -> AwardRecord:
    return AwardRecord(
        fiscal_year=_integer(row.get("PERIODO")),
        modality=_text(row.get("MODALIDAD")),
        contracting_entity=_text(row.get("ENTIDAD")) or "",
        amount=_number(row.get("MONTO")),
        processes_count=_integer(row.get("CONVOCATORIAS")),
    )


class SeaceCdaAdapter(ExtractorPort):
    @property
    def source_name(self) -> str:
        return "SEACE_PENTAHO_CDA"

    async def extract(self, parameter: str) -> dict[str, Any]:
        tax_id = parameter.strip()
        started = time.perf_counter()
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT_S) as client:
            responses = await asyncio.gather(
                *(self._query(client, tax_id, query_id) for query_id in QUERIES.values()),
                return_exceptions=True,
            )
        duration_ms = int((time.perf_counter() - started) * 1000)

        raw: dict[str, dict[str, Any] | None] = {}
        errors: list[str] = []
        for key, response in zip(QUERIES, responses):
            if isinstance(response, BaseException):
                raw[key] = None
                errors.append(f"{QUERIES[key]}: {type(response).__name__}: {response}")
            else:
                raw[key] = response

        profile = ProviderProfile(
            tax_id=tax_id,
            validities=tuple(_validity(r) for r in matrix_to_rows(raw["validities"])),
            shareholders=tuple(_shareholder(r) for r in matrix_to_rows(raw["shareholders"])),
            awards=tuple(_award(r) for r in matrix_to_rows(raw["awards"])),
        )
        if profile.validities or profile.shareholders or profile.awards:
            status = AuditStatus.SUCCESS
        elif errors:
            status = AuditStatus.ERROR
        else:
            status = AuditStatus.NO_DATA

        return {
            "audit": AuditResult(
                source_name=self.source_name,
                query_parameter=tax_id,
                duration_ms=duration_ms,
                status=status,
                details="; ".join(errors) or None,
                executed_at_utc=datetime.now(timezone.utc),
            ),
            "profile": profile,
            "raw": raw,
        }

    @staticmethod
    async def _query(client: httpx.AsyncClient, tax_id: str, query_id: str) -> dict[str, Any]:
        response = await client.post(
            CDA_URL,
            data={
                "path": CDA_PATH,
                "dataAccessId": query_id,
                "paramPARAM_RUC": tax_id,
                "outputIndexId": "1",
                "pageSize": "0",
                "pageStart": "0",
                "paramsearchBox": "",
            },
        )
        response.raise_for_status()
        return response.json()
