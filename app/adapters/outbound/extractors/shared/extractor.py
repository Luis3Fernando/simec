import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, ClassVar, Final, NamedTuple

from app.domain.models.audit import AuditResult, AuditStatus
from app.application.port.out.extractor_port import ExtractorPort

RUC_PATTERN: Final = re.compile(r"[0-9]{11}")
DNI_PATTERN: Final = re.compile(r"[0-9]{8}")


class Outcome(NamedTuple):
    data: Any | None = None
    raw: Any | None = None
    details: str | None = None
    failed: bool = False


class BaseExtractor(ExtractorPort, ABC):
    SOURCE_NAME: ClassVar[str]
    PATTERN: ClassVar[re.Pattern[str]]
    PARAMETER_HINT: ClassVar[str]

    @property
    def source_name(self) -> str:
        return self.SOURCE_NAME

    async def extract(self, parameter: str) -> dict[str, Any]:
        value = parameter.strip()
        started = time.perf_counter()
        if not self.PATTERN.fullmatch(value):
            outcome = Outcome(details=f"Parameter must be {self.PARAMETER_HINT}")
        else:
            try:
                outcome = await self._fetch(value)
            except Exception as exc:
                outcome = Outcome(details=f"{type(exc).__name__}: {exc}", failed=True)

        if outcome.data is not None:
            status = AuditStatus.SUCCESS
        elif outcome.failed:
            status = AuditStatus.ERROR
        else:
            status = AuditStatus.NO_DATA

        return {
            "audit": AuditResult(
                source_name=self.source_name,
                query_parameter=value,
                duration_ms=int((time.perf_counter() - started) * 1000),
                status=status,
                details=outcome.details,
                executed_at_utc=datetime.now(timezone.utc),
            ),
            "data": outcome.data,
            "raw": outcome.raw,
        }

    @abstractmethod
    async def _fetch(self, value: str) -> Outcome: ...
