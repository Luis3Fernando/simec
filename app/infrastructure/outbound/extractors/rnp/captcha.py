import base64
import re
from io import BytesIO
from typing import Final

from PIL import Image, ImageFilter, ImageOps
from playwright.async_api import BrowserContext, Page

CAPTCHA_LENGTH: Final = 6
THRESHOLDS: Final = (135, 115, 155)
UPSCALE_FACTOR: Final = 3
PADDING_PX: Final = 20
NON_ALPHANUMERIC: Final = re.compile(r"[^A-Z0-9]")

OCR_PAGE_HTML: Final = """
<script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
<script>
    window.workerReady = (async () => {
        const worker = await Tesseract.createWorker('eng');
        await worker.setParameters({
            tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            tessedit_pageseg_mode: '7'
        });
        return worker;
    })();
    window.readCaptcha = async (dataUrl) => {
        const worker = await window.workerReady;
        const { data: { text } } = await worker.recognize(dataUrl);
        return text;
    };
</script>
"""


def preprocess_image(image: bytes, threshold: int) -> str:
    gray = Image.open(BytesIO(image)).convert("L")
    gray = gray.resize(
        (gray.width * UPSCALE_FACTOR, gray.height * UPSCALE_FACTOR), Image.Resampling.BICUBIC
    )
    binary = gray.point(lambda pixel: 255 if pixel > threshold else 0)
    cleaned = ImageOps.expand(binary.filter(ImageFilter.MedianFilter(size=3)), border=PADDING_PX, fill=255)
    buffer = BytesIO()
    cleaned.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"


class CaptchaReader:
    def __init__(self, page: Page) -> None:
        self._page = page

    @classmethod
    async def open(cls, context: BrowserContext) -> "CaptchaReader":
        page = await context.new_page()
        await page.set_content(OCR_PAGE_HTML)
        return cls(page)

    async def read(self, image: bytes) -> str | None:
        for threshold in THRESHOLDS:
            raw: str = await self._page.evaluate(
                "dataUrl => window.readCaptcha(dataUrl)", preprocess_image(image, threshold)
            )
            candidate = NON_ALPHANUMERIC.sub("", raw.upper())
            if len(candidate) == CAPTCHA_LENGTH:
                return candidate
        return None
