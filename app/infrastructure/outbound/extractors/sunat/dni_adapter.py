from typing import Final

from app.infrastructure.outbound.extractors.shared.browser import browser_context, run_isolated
from app.infrastructure.outbound.extractors.shared.extractor import DNI_PATTERN, BaseExtractor, Outcome
from app.infrastructure.outbound.extractors.sunat.scraper import (
    RESULT_SELECTOR,
    SEARCH_BUTTON,
    SELECTOR_TIMEOUT_MS,
    open_search_page,
    read_profile,
)
from app.domain.models.sunat import SunatProfile

BY_DOCUMENT_BUTTON: Final = "#btnPorDocumento"
DOCUMENT_INPUT: Final = "#txtNumeroDocumento"
RUC_LINK: Final = "a.aRuc, .list-group-item a[data-ruc], a:has-text('10'), a:has-text('15'), a:has-text('17')"


class SunatDniAdapter(BaseExtractor):
    SOURCE_NAME = "SUNAT_SCRAPER_DNI"
    PATTERN = DNI_PATTERN
    PARAMETER_HINT = "an 8-digit DNI"

    async def _fetch(self, value: str) -> Outcome:
        profile, details = await run_isolated(lambda: self._scrape(value))
        return Outcome(data=profile, details=details)

    @staticmethod
    async def _scrape(dni: str) -> tuple[SunatProfile | None, str | None]:
        async with browser_context() as context:
            page = await open_search_page(context)
            await page.click(BY_DOCUMENT_BUTTON)
            await page.wait_for_selector(DOCUMENT_INPUT, timeout=SELECTOR_TIMEOUT_MS)
            await page.fill(DOCUMENT_INPUT, dni)
            await page.click(SEARCH_BUTTON)

            record_or_link = page.locator(RESULT_SELECTOR).or_(page.locator(RUC_LINK)).first
            await record_or_link.wait_for(timeout=SELECTOR_TIMEOUT_MS)
            if await page.locator(RESULT_SELECTOR).count() == 0:
                await page.locator(RUC_LINK).first.click()
                await page.wait_for_selector(RESULT_SELECTOR, timeout=SELECTOR_TIMEOUT_MS)
            return await read_profile(page, dni)
