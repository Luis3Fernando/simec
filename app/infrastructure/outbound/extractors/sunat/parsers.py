import re
from typing import Final

from bs4 import BeautifulSoup

from app.infrastructure.outbound.extractors.shared.parsing import (
    clean_text,
    optional_text,
    parse_date,
)
from app.domain.models.sunat import BranchOffice, LegalRepresentative, SunatProfile

ACTIVITY_SPLIT: Final = re.compile(r"\s+(?=(?:Principal|Secundaria\s*\d*)\s+-\s)")
LABEL_SPLIT: Final = re.compile(r"\s+Fecha de\b")
START_DATE_LABEL: Final = re.compile(r"Inicio de Actividades:\s*(\d{2}/\d{2}/\d{4})")
RUC_PREFIX: Final = re.compile(r"\d{11}")
TAX_ALERT_KEY: Final = "Alerta Tributaria"

Record = dict[str, str | list[str]]


def parse_record(html: str) -> Record:
    soup = BeautifulSoup(html, "html.parser")
    record: Record = {}

    alert = soup.select_one(".list-group-item-danger")
    if alert:
        record[TAX_ALERT_KEY] = clean_text(alert.get_text())

    for item in soup.select(".list-group-item"):
        if item.find(["button", "form", "input"]):
            continue
        for row in item.select(".row"):
            cols = row.find_all("div", recursive=False)
            if len(cols) == 4:
                for label_col, value_col in ((cols[0], cols[1]), (cols[2], cols[3])):
                    label = clean_text(label_col.get_text())
                    if label.endswith(":"):
                        record[label.rstrip(":")] = clean_text(value_col.get_text())
            elif len(cols) >= 2:
                label = clean_text(cols[0].get_text())
                if not label.endswith(":"):
                    continue
                inner_table = cols[1].find("table")
                if inner_table:
                    lines = [
                        clean_text(tr.get_text())
                        for tr in inner_table.find_all("tr")
                        if clean_text(tr.get_text())
                    ]
                    record[label.rstrip(":")] = lines if len(lines) > 1 else (lines[0] if lines else "-")
                else:
                    record[label.rstrip(":")] = clean_text(cols[1].get_text())
    return record


def _table_rows(html: str, min_columns: int, header_prefixes: tuple[str, ...]) -> list[list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = [[clean_text(td.get_text()) for td in tr.find_all("td")] for tr in soup.find_all("tr")]
    return [
        cols
        for cols in rows
        if len(cols) >= min_columns and not cols[0].casefold().startswith(header_prefixes)
    ]


def parse_representatives(html: str) -> tuple[LegalRepresentative, ...]:
    return tuple(
        LegalRepresentative(
            document_type=cols[0],
            document_number=cols[1],
            full_name=cols[2],
            role=cols[3],
            start_date=parse_date(cols[4]),
        )
        for cols in _table_rows(html, 5, ("documento",))
    )


def parse_branch_offices(html: str) -> tuple[BranchOffice, ...]:
    return tuple(
        BranchOffice(
            code=cols[0],
            establishment_type=cols[1],
            address=cols[2],
            economic_activity=cols[3],
        )
        for cols in _table_rows(html, 4, ("código", "codigo"))
    )


def lookup(record: Record, prefix: str) -> str | None:
    for key, value in record.items():
        if key.casefold().startswith(prefix.casefold()):
            return optional_text(" ".join(value) if isinstance(value, list) else value)
    return None


def extract_ruc(record: Record) -> str | None:
    match = RUC_PREFIX.match(lookup(record, "Número de RUC") or "")
    return match.group() if match else None


def _activities(record: Record) -> tuple[str, ...]:
    for key, value in record.items():
        if key.casefold().startswith("actividad(es) económica"):
            if isinstance(value, list):
                return tuple(value)
            return tuple(a for a in ACTIVITY_SPLIT.split(value) if a)
    return ()


def build_profile(
    tax_id: str,
    record: Record,
    representatives: tuple[LegalRepresentative, ...],
    branch_offices: tuple[BranchOffice, ...],
) -> SunatProfile:
    registration = lookup(record, "Fecha de Inscripción")
    start_match = START_DATE_LABEL.search(registration or "")
    status = lookup(record, "Estado del Contribuyente")
    return SunatProfile(
        tax_id=tax_id,
        taxpayer_type=lookup(record, "Tipo Contribuyente"),
        commercial_name=lookup(record, "Nombre Comercial"),
        registration_date=parse_date(registration),
        activity_start_date=parse_date(
            lookup(record, "Fecha de Inicio de Actividades") or (start_match.group(1) if start_match else None)
        ),
        status=(LABEL_SPLIT.split(status, maxsplit=1)[0] or None) if status else None,
        condition=lookup(record, "Condición del Contribuyente"),
        tax_alert=record.get(TAX_ALERT_KEY) if isinstance(record.get(TAX_ALERT_KEY), str) else None,
        fiscal_address=lookup(record, "Domicilio Fiscal"),
        economic_activities=_activities(record),
        electronic_issuance=lookup(record, "Sistema de Emisión Electrónica"),
        legal_representatives=representatives,
        branch_offices=branch_offices,
    )
