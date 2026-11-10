import asyncio
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Final

from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, Playwright, async_playwright

from app.domain.models.provider import AuditResult, AuditStatus, SunatProfile
from app.domain.ports.outbound.extractor_port import ExtractorPort

SUNAT_URL: Final = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BROWSER_CHANNELS: Final = ("chrome", "msedge", None)
BROWSER_ARGS: Final = ["--disable-blink-features=AutomationControlled"]
HIDE_WEBDRIVER_SCRIPT: Final = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
NAVIGATION_TIMEOUT_MS: Final = 30_000
SELECTOR_TIMEOUT_MS: Final = 30_000
RUC_INPUT_SELECTOR: Final = "#txtRuc"
SEARCH_BUTTON_SELECTOR: Final = "#btnAceptar"
RESULT_SELECTOR: Final = "text=Número de RUC:"
REPRESENTATIVES_BUTTON: Final = "Representante"
BRANCH_OFFICES_BUTTON: Final = "Establecimiento"

BUTTON_RESPONSE_SCRIPT: Final = """
async (buttonText) => {
    const buttons = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]'));
    const button = buttons.find(b => (b.innerText || b.value || '').includes(buttonText));
    if (!button) return "";

    return new Promise((resolve) => {
        const originalSubmit = HTMLFormElement.prototype.submit;
        HTMLFormElement.prototype.submit = function () {
            const body = new URLSearchParams(new FormData(this)).toString();
            const actionUrl = this.action || 'jcrS00Alias';
            HTMLFormElement.prototype.submit = originalSubmit;
            fetch(actionUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body,
            })
                .then(response => response.arrayBuffer())
                .then(buffer => resolve(new TextDecoder('iso-8859-1').decode(buffer)))
                .catch(() => resolve(""));
        };
        button.click();
        setTimeout(() => {
            HTMLFormElement.prototype.submit = originalSubmit;
            resolve("");
        }, 5000);
    });
}
"""

CHALLENGE_MARKER: Final = "security verification"
RUC_PATTERN: Final = re.compile(r"[0-9]{11}")
DATE_PATTERN: Final = re.compile(r"\d{2}/\d{2}/\d{4}")
ACTIVITY_SPLIT: Final = re.compile(r"\s+(?=(?:Principal|Secundaria\s*\d*)\s+-\s)")
LABEL_SPLIT: Final = re.compile(r"\s+Fecha de\b")

Record = dict[str, str | list[str]]


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text).strip() if text else ""


def parse_record(html: str) -> Record:
    soup = BeautifulSoup(html, "html.parser")
    record: Record = {}

    alert = soup.select_one(".list-group-item-danger")
    if alert:
        record["Alerta Tributaria"] = _clean(alert.get_text())

    for item in soup.select(".list-group-item"):
        if item.find(["button", "form", "input"]):
            continue
        for row in item.select(".row"):
            cols = row.find_all("div", recursive=False)
            if len(cols) == 4:
                for label_col, value_col in ((cols[0], cols[1]), (cols[2], cols[3])):
                    label = _clean(label_col.get_text())
                    if label.endswith(":"):
                        record[label.rstrip(":")] = _clean(value_col.get_text())
            elif len(cols) >= 2:
                label = _clean(cols[0].get_text())
                if not label.endswith(":"):
                    continue
                inner_table = cols[1].find("table")
                if inner_table:
                    lines = [
                        _clean(tr.get_text())
                        for tr in inner_table.find_all("tr")
                        if _clean(tr.get_text())
                    ]
                    record[label.rstrip(":")] = lines if len(lines) > 1 else (lines[0] if lines else "-")
                else:
                    record[label.rstrip(":")] = _clean(cols[1].get_text())
    return record


def _table_rows(html: str, min_columns: int, header_prefixes: tuple[str, ...]) -> list[list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = [[_clean(td.get_text()) for td in tr.find_all("td")] for tr in soup.find_all("tr")]
    return [
        cols
        for cols in rows
        if len(cols) >= min_columns and not cols[0].casefold().startswith(header_prefixes)
    ]


def parse_representatives(html: str) -> list[dict[str, Any]]:
    return [
        {
            "document_type": cols[0],
            "document_number": cols[1],
            "full_name": cols[2],
            "role": cols[3],
            "start_date": cols[4],
        }
        for cols in _table_rows(html, 5, ("documento",))
    ]


def parse_branch_offices(html: str) -> list[dict[str, Any]]:
    return [
        {
            "code": cols[0],
            "establishment_type": cols[1],
            "address": cols[2],
            "economic_activity": cols[3],
        }
        for cols in _table_rows(html, 4, ("código", "codigo"))
    ]


def _lookup(record: Record, prefix: str) -> str | None:
    for key, value in record.items():
        if key.casefold().startswith(prefix.casefold()):
            text = " ".join(value) if isinstance(value, list) else value
            return text or None
    return None


def _first_date(text: str | None) -> str | None:
    match = DATE_PATTERN.search(text) if text else None
    return match.group() if match else None


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
    tax_id: str,
    record: Record,
    representatives: list[dict[str, Any]],
    branch_offices: list[dict[str, Any]],
) -> SunatProfile:
    return SunatProfile(
        tax_id=tax_id,
        taxpayer_type=_lookup(record, "Tipo Contribuyente"),
        commercial_name=_lookup(record, "Nombre Comercial"),
        registration_date=_first_date(_lookup(record, "Fecha de Inscripción")),
        activity_start_date=_first_date(_lookup(record, "Fecha de Inicio de Actividades")),
        status=_before_label(_lookup(record, "Estado del Contribuyente")),
        condition=_lookup(record, "Condición del Contribuyente"),
        fiscal_address=_lookup(record, "Domicilio Fiscal"),
        economic_activities=_activities(record),
        electronic_issuance=_lookup(record, "Sistema de Emisión Electrónica"),
        legal_representatives=representatives,
        branch_offices=branch_offices,
    )


async def _launch_browser(playwright: Playwright) -> Browser:
    last_error: Exception | None = None
    for channel in BROWSER_CHANNELS:
        try:
            return await playwright.chromium.launch(
                headless=True, channel=channel, args=BROWSER_ARGS
            )
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"No supported browser available: {last_error}")


async def _button_html(page: Page, button_text: str) -> str:
    html: str = await page.evaluate(BUTTON_RESPONSE_SCRIPT, button_text)
    if CHALLENGE_MARKER in html.casefold():
        raise RuntimeError("Blocked by SUNAT security verification (Cloudflare)")
    return html


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
            browser = await _launch_browser(playwright)
            try:
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1366, "height": 768},
                    locale="es-PE",
                )
                await context.add_init_script(HIDE_WEBDRIVER_SCRIPT)
                page = await context.new_page()
                await page.goto(SUNAT_URL, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
                await page.wait_for_selector(RUC_INPUT_SELECTOR, timeout=SELECTOR_TIMEOUT_MS)
                await page.fill(RUC_INPUT_SELECTOR, tax_id)
                await page.click(SEARCH_BUTTON_SELECTOR)
                await page.wait_for_selector(RESULT_SELECTOR, timeout=SELECTOR_TIMEOUT_MS)

                record = parse_record(await page.content())
                if not record:
                    return None, None

                notes: list[str] = []
                representatives: list[dict[str, Any]] = []
                branch_offices: list[dict[str, Any]] = []
                try:
                    representatives = parse_representatives(
                        await _button_html(page, REPRESENTATIVES_BUTTON)
                    )
                except Exception as exc:
                    notes.append(f"Legal representatives unavailable: {type(exc).__name__}: {exc}")
                try:
                    branch_offices = parse_branch_offices(
                        await _button_html(page, BRANCH_OFFICES_BUTTON)
                    )
                except Exception as exc:
                    notes.append(f"Branch offices unavailable: {type(exc).__name__}: {exc}")

                profile = build_profile(tax_id, record, representatives, branch_offices)
                return profile, "; ".join(notes) or None
            finally:
                await browser.close()
