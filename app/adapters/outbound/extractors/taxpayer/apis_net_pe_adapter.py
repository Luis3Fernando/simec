import time
from datetime import datetime, timezone
from typing import Any, Final

import httpx

from app.domain.models.provider import AuditResult, AuditStatus, TaxpayerDetails
from app.domain.ports.outbound.extractor_port import ExtractorPort

BASE_URL: Final = "https://api.apis.net.pe/v1"
TIMEOUT_S: Final = 15.0
HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://apis.net.pe/",
}
ENDPOINTS: Final = {8: ("dni", "DNI"), 11: ("ruc", "RUC")}
NO_DATA_CODES: Final = frozenset({404, 422})


def _text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _to_details(document_type: str, parameter: str, data: dict[str, Any]) -> TaxpayerDetails:
    first_surname = _text(data.get("apellidoPaterno"))
    second_surname = _text(data.get("apellidoMaterno"))
    given_names = _text(data.get("nombres"))
    full_name = " ".join(p for p in (first_surname, second_surname, given_names) if p)
    return TaxpayerDetails(
        document_type=document_type,
        document_number=_text(data.get("numeroDocumento")) or parameter,
        legal_name=_text(data.get("nombre")) or full_name,
        tax_status=_text(data.get("estado")),
        tax_condition=_text(data.get("condicion")),
        fiscal_address=_text(data.get("direccion")),
        ubigeo=_text(data.get("ubigeo")),
        department=_text(data.get("departamento")),
        province=_text(data.get("provincia")),
        district=_text(data.get("distrito")),
        first_surname=first_surname,
        second_surname=second_surname,
        given_names=given_names,
    )


class ApisNetPeAdapter(ExtractorPort):
    @property
    def source_name(self) -> str:
        return "APIS_NET_PE"

    async def extract(self, parameter: str) -> dict[str, Any]:
        number = parameter.strip()
        started = time.perf_counter()
        details: TaxpayerDetails | None = None
        raw: dict[str, Any] | None = None
        status = AuditStatus.ERROR
        error: str | None = None

        endpoint = ENDPOINTS.get(len(number)) if number.isdigit() else None
        if endpoint is None:
            error = "Parameter must be a DNI (8 digits) or RUC (11 digits)"
        else:
            path, document_type = endpoint
            try:
                async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT_S) as client:
                    response = await client.get(f"{BASE_URL}/{path}", params={"numero": number})
                if response.status_code in NO_DATA_CODES:
                    status = AuditStatus.NO_DATA
                    error = f"HTTP {response.status_code}"
                else:
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, dict):
                        raise ValueError("Unexpected response payload")
                    raw = payload
                    details = _to_details(document_type, number, payload)
                    status = AuditStatus.SUCCESS
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"

        return {
            "audit": AuditResult(
                source_name=self.source_name,
                query_parameter=number,
                duration_ms=int((time.perf_counter() - started) * 1000),
                status=status,
                details=error,
                executed_at_utc=datetime.now(timezone.utc),
            ),
            "taxpayer_details": details,
            "raw": raw,
        }
