import asyncio
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Final

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext, Page, async_playwright

from app.domain.models.provider import AuditResult, AuditStatus, SunatProfile
from app.domain.ports.outbound.extractor_port import ExtractorPort

SUNAT_URL: Final = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
SELECTOR_TIMEOUT_MS: Final = 30_000
REPRESENTATIVES_TIMEOUT_MS: Final = 8_000
POPUP_TIMEOUT_MS: Final = 5_000
INPUT_SELECTOR: Final = "input#txtRuc, input[name='search1'], input[placeholder*='RUC']"
SEARCH_SELECTOR: Final = "button#btnAceptar, button:has-text('Buscar'), input[value='Buscar']"
RESULT_SELECTOR: Final = "text=Número de RUC:"
REPRESENTATIVES_SELECTOR: Final = (
    "button:has-text('Representante(s) Legal(es)'), input[value*='Representante']"
)
REPRESENTATIVES_HEADER_SELECTOR: Final = "text=Cargo"

RUC_PATTERN: Final = re.compile(r"[0-9]{11}")
DATE_PATTERN: Final = re.compile(r"\d{2}/\d{2}/\d{4}")
START_DATE_PATTERN: Final = re.compile(r"Inicio de Actividades:\s*(\d{2}/\d{2}/\d{4})")
ACTIVITY_SPLIT: Final = re.compile(r"\s+(?=(?:Principal|Secundaria\s*\d*)\s+-\s)")
LABEL_SPLIT: Final = re.compile(r"\s+Fecha de\b")

Record = dict[str, str | list[str]]


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text).strip() if text else ""


def parse_record(html: str) -> Record:
    soup = BeautifulSoup(html, "html.parser")
    record: Record = {}
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        index = 0
        while index < len(cells):
            label = _clean(cells[index].get_text())
            if label.endswith(":") and index + 1 < len(cells):
                paragraphs = [
                    _clean(p.get_text())
                    for p in cells[index + 1].find_all(["p", "div"])
                    if _clean(p.get_text())
                ]
                record[label.rstrip(":")] = (
                    paragraphs if len(paragraphs) > 1 else _clean(cells[index + 1].get_text())
                )
                index += 2
            else:
                index += 1
    for item in soup.find_all("div", class_=re.compile(r"list-group-item")):
        key, separator, value = _clean(item.get_text()).partition(":")
        if separator and _clean(key) not in record:
            record[_clean(key)] = _clean(value)
    return record


def parse_representatives(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    representatives: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        if "cargo" not in table.get_text().casefold():
            continue
        for row in table.find_all("tr"):
            cols = [_clean(td.get_text()) for td in row.find_all("td")]
            if len(cols) >= 4 and "cargo" not in (c.casefold() for c in cols):
                representatives.append(
                    {
                        "document_type": cols[0],
                        "document_number": cols[1],
                        "full_name": cols[2],
                        "role": cols[3],
                        "start_date": cols[4] if len(cols) >= 5 else None,
                    }
                )
    return representatives


def _lookup(record: Record, prefix: str) -> str | None:
    for key, value in record.items():
        if key.casefold().startswith(prefix.casefold()):
            text = " ".join(value) if isinstance(value, list) else value
            return text or None
    return None


def _before_label(text: str | None) -> str | None:
    return (LABEL_SPLIT.split(text, maxsplit=1)[0] or None) if text else None


def _activities(record: Record) -> list[str]:
    for key, value in record.items():
        if key.casefold().startswith("actividad(es) económica"):
            if isinstance(value, list):
                return value
            return [a for a in ACTIVITY_SPLIT.split(value) if a]
    return []


def build_profile(
    tax_id: str, record: Record, representatives: list[dict[str, Any]]
) -> SunatProfile:
    registration = _lookup(record, "Fecha de Inscripción") or ""
    registration_match = DATE_PATTERN.search(registration)
    start_match = START_DATE_PATTERN.search(registration)
    start_text = _lookup(record, "Fecha de Inicio de Actividades")
    start_date = start_match.group(1) if start_match else (
        match.group() if start_text and (match := DATE_PATTERN.search(start_text)) else None
    )
    return SunatProfile(
        tax_id=tax_id,
        taxpayer_type=_lookup(record, "Tipo Contribuyente"),
        commercial_name=_lookup(record, "Nombre Comercial"),
        registration_date=registration_match.group() if registration_match else None,
        activity_start_date=start_date,
        status=_before_label(_lookup(record, "Estado del Contribuyente")),
        condition=_lookup(record, "Condición del Contribuyente"),
        fiscal_address=_lookup(record, "Domicilio Fiscal"),
        economic_activities=_activities(record),
        electronic_issuance=_lookup(record, "Sistema de Emisión Electrónica"),
        legal_representatives=representatives,
    )


async def _fetch_representatives_html(page: Page, context: BrowserContext) -> str:
    try:
        async with context.expect_page(timeout=POPUP_TIMEOUT_MS) as popup_info:
            await page.click(REPRESENTATIVES_SELECTOR)
        popup = await popup_info.value
        await popup.wait_for_load_state("domcontentloaded")
        html = await popup.content()
        await popup.close()
        return html
    except Exception:
        await page.wait_for_selector(
            REPRESENTATIVES_HEADER_SELECTOR, timeout=REPRESENTATIVES_TIMEOUT_MS
        )
        return await page.content()


class SunatScraperAdapter(ExtractorPort):
    @property
    def source_name(self) -> str:
        return "SUNAT_SCRAPER"

    async def extract(self, parameter: str) -> dict[str, Any]:
        tax_id = parameter.strip()
        started = time.perf_counter()
        profile: SunatProfile | None = None
        status = AuditStatus.NO_DATA
        details: str | None = "Parameter is not an 11-digit RUC"

        if RUC_PATTERN.fullmatch(tax_id):
            try:
                profile, details = await self._scrape_isolated(tax_id)
                status = AuditStatus.SUCCESS if profile else AuditStatus.NO_DATA
            except Exception as exc:
                status = AuditStatus.ERROR
                details = f"{type(exc).__name__}: {exc}"

        return {
            "audit": AuditResult(
                source_name=self.source_name,
                query_parameter=tax_id,
                duration_ms=int((time.perf_counter() - started) * 1000),
                status=status,
                details=details,
                executed_at_utc=datetime.now(timezone.utc),
            ),
            "sunat_profile": profile,
        }

    @classmethod
    async def _scrape_isolated(cls, tax_id: str) -> tuple[SunatProfile | None, str | None]:
        if sys.platform == "win32" and not isinstance(
            asyncio.get_running_loop(), asyncio.ProactorEventLoop
        ):
            return await asyncio.to_thread(cls._scrape_in_proactor_loop, tax_id)
        return await cls._scrape(tax_id)

    @classmethod
    def _scrape_in_proactor_loop(cls, tax_id: str) -> tuple[SunatProfile | None, str | None]:
        loop = asyncio.ProactorEventLoop()
        try:
            return loop.run_until_complete(cls._scrape(tax_id))
        finally:
            loop.close()

    @staticmethod
    async def _scrape(tax_id: str) -> tuple[SunatProfile | None, str | None]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                context = await browser.new_context(user_agent=USER_AGENT)
                page = await context.new_page()
                await page.goto(SUNAT_URL, wait_until="domcontentloaded", timeout=SELECTOR_TIMEOUT_MS)
                await page.wait_for_selector(INPUT_SELECTOR, timeout=SELECTOR_TIMEOUT_MS)
                await page.fill(INPUT_SELECTOR, tax_id)
                await page.click(SEARCH_SELECTOR)
                await page.wait_for_selector(RESULT_SELECTOR, timeout=SELECTOR_TIMEOUT_MS)
                record = parse_record(await page.content())
                if not record:
                    return None, None

                representatives: list[dict[str, Any]] = []
                details: str | None = None
                if await page.query_selector(REPRESENTATIVES_SELECTOR):
                    try:
                        representatives = parse_representatives(
                            await _fetch_representatives_html(page, context)
                        )
                    except Exception as exc:
                        details = f"Legal representatives unavailable: {type(exc).__name__}: {exc}"
                return build_profile(tax_id, record, representatives), details
            finally:
                await browser.close()
