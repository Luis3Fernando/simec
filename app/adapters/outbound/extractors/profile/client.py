from abc import ABC, abstractmethod
from typing import Any, ClassVar, Final

import httpx

from app.adapters.outbound.extractors.shared.extractor import BaseExtractor, Outcome

BASE_URL: Final = "https://api.apis.net.pe/v1"
TIMEOUT_S: Final = 15.0
HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://apis.net.pe/",
}
NO_DATA_CODES: Final = frozenset({404, 422})


class ApisNetPeExtractor(BaseExtractor, ABC):
    ENDPOINT: ClassVar[str]

    async def _fetch(self, value: str) -> Outcome:
        async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT_S) as client:
            response = await client.get(f"{BASE_URL}/{self.ENDPOINT}", params={"numero": value})
        if response.status_code in NO_DATA_CODES:
            return Outcome(details=f"HTTP {response.status_code}")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected response payload")
        data = self._map(payload, value)
        return Outcome(
            data=data, raw=payload, details=None if data is not None else "Empty record"
        )

    @abstractmethod
    def _map(self, payload: dict[str, Any], value: str) -> Any | None: ...
