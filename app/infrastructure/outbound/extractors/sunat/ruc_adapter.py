from app.infrastructure.outbound.extractors.shared.browser import browser_context, run_isolated
from app.infrastructure.outbound.extractors.shared.extractor import RUC_PATTERN, BaseExtractor, Outcome
from app.infrastructure.outbound.extractors.sunat.scraper import (
    RESULT_SELECTOR,
    SEARCH_BUTTON,
    SELECTOR_TIMEOUT_MS,
    open_search_page,
    read_profile,
)
from app.domain.models.sunat import SunatProfile

RUC_INPUT: str = "#txtRuc"


class SunatRucAdapter(BaseExtractor):
    SOURCE_NAME = "SUNAT_SCRAPER_RUC"
    PATTERN = RUC_PATTERN
    PARAMETER_HINT = "an 11-digit RUC"

    async def _fetch(self, value: str) -> Outcome:
        profile, details = await run_isolated(lambda: self._scrape(value))
        return Outcome(data=profile, details=details)

    @staticmethod
    async def _scrape(ruc: str) -> tuple[SunatProfile | None, str | None]:
        async with browser_context() as context:
            page = await open_search_page(context)
            await page.wait_for_selector(RUC_INPUT, timeout=SELECTOR_TIMEOUT_MS)
            await page.fill(RUC_INPUT, ruc)
            await page.click(SEARCH_BUTTON)
            await page.wait_for_selector(RESULT_SELECTOR, timeout=SELECTOR_TIMEOUT_MS)
            return await read_profile(page, ruc)
