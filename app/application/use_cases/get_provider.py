import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from app.domain.models.provider import (
    AuditResult,
    AuditStatus,
    ProviderProfile,
    ProviderReport,
)
from app.domain.ports.inbound.get_provider_port import GetProviderPort
from app.domain.ports.outbound.extractor_port import ExtractorPort


class GetProviderUseCase(GetProviderPort):
    def __init__(self, extractors: list[ExtractorPort]) -> None:
        self._extractors = list(extractors)

    async def get_provider(self, tax_id: str) -> ProviderReport:
        tax_id = tax_id.strip()
        started = time.perf_counter()
        responses = await asyncio.gather(
            *(e.extract(tax_id) for e in self._extractors),
            return_exceptions=True,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)

        profiles: list[ProviderProfile] = []
        audit_entries: list[AuditResult] = []
        for extractor, response in zip(self._extractors, responses):
            try:
                if isinstance(response, BaseException):
                    raise response
                audit, profile = self._unpack(response)
            except Exception as exc:
                audit_entries.append(
                    AuditResult(
                        source_name=extractor.source_name,
                        query_parameter=tax_id,
                        duration_ms=duration_ms,
                        status=AuditStatus.ERROR,
                        details=f"{type(exc).__name__}: {exc}",
                        executed_at_utc=datetime.now(timezone.utc),
                    )
                )
                continue
            audit_entries.append(audit)
            profiles.append(profile)

        return ProviderReport(
            profile=self._merge(tax_id, profiles),
            audit_entries=tuple(audit_entries),
        )

    @staticmethod
    def _unpack(response: dict[str, Any]) -> tuple[AuditResult, ProviderProfile]:
        audit = response.get("audit")
        profile = response.get("profile")
        if not isinstance(audit, AuditResult) or not isinstance(profile, ProviderProfile):
            raise ValueError("Extractor response lacks valid 'audit' or 'profile'")
        return audit, profile

    @staticmethod
    def _merge(tax_id: str, profiles: list[ProviderProfile]) -> ProviderProfile:
        return ProviderProfile(
            tax_id=tax_id,
            validities=tuple(v for p in profiles for v in p.validities),
            shareholders=tuple(s for p in profiles for s in p.shareholders),
            awards=tuple(a for p in profiles for a in p.awards),
        )
