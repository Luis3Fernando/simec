from typing import Final

from playwright.async_api import Page

from app.adapters.outbound.extractors.rnp.captcha import CaptchaReader
from app.adapters.outbound.extractors.rnp.parser import has_no_records, parse_record
from app.adapters.outbound.extractors.shared.browser import browser_context, run_isolated
from app.adapters.outbound.extractors.shared.extractor import RUC_PATTERN, BaseExtractor, Outcome

RNP_URL: Final = "https://www.rnp.gob.pe/Constancia/RNP_Constancia/ConsultaRuc.asp"
NAVIGATION_TIMEOUT_MS: Final = 30_000
SUBMIT_TIMEOUT_MS: Final = 15_000
REFRESH_DELAY_MS: Final = 350
DEFAULT_MAX_ATTEMPTS: Final = 12
TEXT_INPUT: Final = "input[type='text']"
CAPTCHA_IMAGE: Final = "img[src*='captcha' i], img[src*='codigo' i], form img"
SEARCH_BUTTON: Final = "input[value='Buscar'], button:has-text('Buscar')"
REFRESH_LINK: Final = "a:has-text('Refrescar')"


class RnpRucAdapter(BaseExtractor):
    SOURCE_NAME = "RNP_SCRAPER_RUC"
    PATTERN = RUC_PATTERN
    PARAMETER_HINT = "an 11-digit RUC"

    def __init__(self, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> None:
        self._max_attempts = max_attempts

    async def _fetch(self, value: str) -> Outcome:
        return await run_isolated(lambda: self._scrape(value))

    async def _scrape(self, ruc: str) -> Outcome:
        async with browser_context() as context:
            page = await context.new_page()
            reader = await CaptchaReader.open(context)
            await page.goto(RNP_URL, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)

            for _ in range(self._max_attempts):
                await page.locator(TEXT_INPUT).first.fill(ruc)
                image = await page.locator(CAPTCHA_IMAGE).first.screenshot()
                code = await reader.read(image)
                if code is None:
                    await self._refresh_captcha(page)
                    continue

                await page.locator(TEXT_INPUT).nth(1).fill(code)
                async with page.expect_navigation(
                    wait_until="domcontentloaded", timeout=SUBMIT_TIMEOUT_MS
                ):
                    await page.locator(SEARCH_BUTTON).first.click()

                html = await page.content()
                if has_no_records(html):
                    return Outcome(details="No RNP registrations for this RUC")
                record = parse_record(html)
                if record is not None:
                    return Outcome(data=record)

        return Outcome(
            details=f"CAPTCHA not accepted after {self._max_attempts} attempts", failed=True
        )

    @staticmethod
    async def _refresh_captcha(page: Page) -> None:
        refresh = page.locator(REFRESH_LINK).first
        if await refresh.count() > 0:
            await refresh.click()
            await page.wait_for_timeout(REFRESH_DELAY_MS)
