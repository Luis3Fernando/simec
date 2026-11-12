import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Mapping, NamedTuple, TypeVar

from app.application.port.out.extractor_port import ExtractorPort
from app.domain.models.audit import AuditResult, AuditStatus

T = TypeVar("T")

DEFAULT_TIMEOUT_S = 120.0


class SourceResult(NamedTuple):
    audit: AuditResult
    data: Any | None

    def data_as(self, kind: type[T]) -> T | None:
        return self.data if isinstance(self.data, kind) else None


async def _run_source(extractor: ExtractorPort, parameter: str, timeout_s: float) -> SourceResult:
    started = time.perf_counter()
    try:
        response = await asyncio.wait_for(extractor.extract(parameter), timeout_s)
        audit = response.get("audit")
        if not isinstance(audit, AuditResult):
            raise ValueError("Extractor response lacks a valid 'audit'")
        return SourceResult(audit, response.get("data"))
    except Exception as exc:
        details = (
            f"Timed out after {timeout_s:g}s"
            if isinstance(exc, TimeoutError)
            else f"{type(exc).__name__}: {exc}"
        )
        return SourceResult(
            AuditResult(
                source_name=extractor.source_name,
                query_parameter=parameter,
                duration_ms=int((time.perf_counter() - started) * 1000),
                status=AuditStatus.ERROR,
                details=details,
                executed_at_utc=datetime.now(timezone.utc),
            ),
            None,
        )


async def run_sources(
    sources: Mapping[str, ExtractorPort], parameter: str, timeout_s: float = DEFAULT_TIMEOUT_S
) -> dict[str, SourceResult]:
    results = await asyncio.gather(
        *(_run_source(extractor, parameter, timeout_s) for extractor in sources.values())
    )
    return dict(zip(sources, results))
