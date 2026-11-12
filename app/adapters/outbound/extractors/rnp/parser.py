from typing import Final

from bs4 import BeautifulSoup

from app.adapters.outbound.extractors.shared.parsing import clean_text, optional_text, parse_date
from app.domain.models.rnp import RnpRecord, RnpRegistration

NO_RECORDS_MARKERS: Final = ("NO SE ENCONTRO INFORMACION", "NO REGISTRA")
RESULT_MARKERS: Final = ("INSCRIPCION EN EL RNP", "PROVEEDOR")
CHAPTER_MARKER: Final = "INSCRIPCION EN EL RNP"


def has_no_records(html: str) -> bool:
    text = clean_text(BeautifulSoup(html, "html.parser").get_text()).upper()
    return any(marker in text for marker in NO_RECORDS_MARKERS)


def parse_record(html: str) -> RnpRecord | None:
    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup.get_text()).upper()
    if not any(marker in text for marker in RESULT_MARKERS):
        return None

    ruc: str | None = None
    business_name: str | None = None
    registrations: list[dict[str, str | None]] = []
    current: dict[str, str | None] | None = None

    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        row_text = clean_text(row.get_text()).upper()

        if CHAPTER_MARKER in row_text and len(cells) == 1:
            parts = row_text.split("-")
            current = {"chapter": parts[-1].strip() if len(parts) > 1 else row_text}
            registrations.append(current)
            continue

        if len(cells) >= 2:
            label = clean_text(cells[0].get_text()).upper()
            value = optional_text(cells[1].get_text())
            if label.startswith("RUC"):
                ruc = value
            elif label.startswith("NOMBRE"):
                business_name = value
            elif current is not None:
                if "PROVEEDOR" in label:
                    current["provider_code"] = value
                elif "PAGO" in label:
                    current["payment_date"] = value
                elif "TRAMITE" in label or "CARGO" in label:
                    current["procedure_number"] = value
                elif "ESTADO" in label:
                    current["status"] = value
                elif "MOTIVO" in label:
                    current["reason"] = value

    if ruc is None:
        return None
    return RnpRecord(
        ruc=ruc,
        business_name=business_name,
        registrations=tuple(
            RnpRegistration(
                chapter=item["chapter"] or "",
                provider_code=item.get("provider_code"),
                payment_date=parse_date(item.get("payment_date")),
                procedure_number=item.get("procedure_number"),
                status=item.get("status"),
                reason=item.get("reason"),
            )
            for item in registrations
        ),
    )
