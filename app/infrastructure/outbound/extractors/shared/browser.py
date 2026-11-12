import asyncio
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable, Final, TypeVar

from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

T = TypeVar("T")

USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BROWSER_CHANNELS: Final = ("chrome", "msedge", None)
BROWSER_ARGS: Final = ["--disable-blink-features=AutomationControlled"]
HIDE_WEBDRIVER_SCRIPT: Final = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
VIEWPORT: Final = {"width": 1366, "height": 768}
LOCALE: Final = "es-PE"


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


@asynccontextmanager
async def browser_context() -> AsyncIterator[BrowserContext]:
    async with async_playwright() as playwright:
        browser = await _launch_browser(playwright)
        try:
            context = await browser.new_context(
                user_agent=USER_AGENT, viewport=VIEWPORT, locale=LOCALE
            )
            await context.add_init_script(HIDE_WEBDRIVER_SCRIPT)
            yield context
        finally:
            await browser.close()


def _run_in_proactor_loop(task: Callable[[], Awaitable[T]]) -> T:
    async def runner() -> T:
        return await task()

    loop = asyncio.ProactorEventLoop()
    try:
        return loop.run_until_complete(runner())
    finally:
        loop.close()


async def run_isolated(task: Callable[[], Awaitable[T]]) -> T:
    if sys.platform == "win32" and not isinstance(
        asyncio.get_running_loop(), asyncio.ProactorEventLoop
    ):
        return await asyncio.to_thread(_run_in_proactor_loop, task)
    return await task()
