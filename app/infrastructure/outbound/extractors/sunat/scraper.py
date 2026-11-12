from typing import Final

from playwright.async_api import BrowserContext, Page

from app.infrastructure.outbound.extractors.sunat.parsers import (
    build_profile,
    extract_ruc,
    parse_branch_offices,
    parse_record,
    parse_representatives,
)
from app.domain.models.sunat import BranchOffice, LegalRepresentative, SunatProfile

SUNAT_URL: Final = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
NAVIGATION_TIMEOUT_MS: Final = 30_000
SELECTOR_TIMEOUT_MS: Final = 30_000
SEARCH_BUTTON: Final = "#btnAceptar"
RESULT_SELECTOR: Final = "text=Número de RUC:"
REPRESENTATIVES_BUTTON: Final = "Representante"
BRANCH_OFFICES_BUTTON: Final = "Establecimiento"
CHALLENGE_MARKER: Final = "security verification"

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


async def open_search_page(context: BrowserContext) -> Page:
    page = await context.new_page()
    await page.goto(SUNAT_URL, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
    return page


async def _button_html(page: Page, button_text: str) -> str:
    html: str = await page.evaluate(BUTTON_RESPONSE_SCRIPT, button_text)
    if CHALLENGE_MARKER in html.casefold():
        raise RuntimeError("Blocked by SUNAT security verification (Cloudflare)")
    return html


async def read_profile(page: Page, fallback_tax_id: str) -> tuple[SunatProfile | None, str | None]:
    record = parse_record(await page.content())
    if not record:
        return None, None

    notes: list[str] = []
    representatives: tuple[LegalRepresentative, ...] = ()
    branch_offices: tuple[BranchOffice, ...] = ()
    try:
        representatives = parse_representatives(await _button_html(page, REPRESENTATIVES_BUTTON))
    except Exception as exc:
        notes.append(f"Legal representatives unavailable: {type(exc).__name__}: {exc}")
    try:
        branch_offices = parse_branch_offices(await _button_html(page, BRANCH_OFFICES_BUTTON))
    except Exception as exc:
        notes.append(f"Branch offices unavailable: {type(exc).__name__}: {exc}")

    tax_id = extract_ruc(record) or fallback_tax_id
    return build_profile(tax_id, record, representatives, branch_offices), "; ".join(notes) or None
