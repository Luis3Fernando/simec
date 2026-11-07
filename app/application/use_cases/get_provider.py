import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Final

from app.domain.models.provider import (
    AuditResult,
    AuditStatus,
    ProviderProfile,
    ProviderReport,
    TaxpayerDetails,
)
from app.domain.ports.inbound.get_provider_port import GetProviderPort
from app.domain.ports.outbound.extractor_port import ExtractorPort

DEFAULT_TIMEOUT_S: Final = 30.0


class GetProviderUseCase(GetProviderPort):
    def __init__(
        self,
        extractors: list[ExtractorPort],
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._extractors = list(extractors)
        self._timeout_s = timeout_s

    async def get_provider(self, tax_id: str) -> ProviderReport:
        tax_id = tax_id.strip()
        started = time.perf_counter()
        responses = await asyncio.gather(
            *(asyncio.wait_for(e.extract(tax_id), self._timeout_s) for e in self._extractors),
            return_exceptions=True,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)

        profiles: list[ProviderProfile] = []
        details: list[TaxpayerDetails] = []
        audit_entries: list[AuditResult] = []
        for extractor, response in zip(self._extractors, responses):
            try:
                if isinstance(response, BaseException):
                    raise response
                audit, profile, taxpayer = self._unpack(response)
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
            if profile is not None:
                profiles.append(profile)
            if taxpayer is not None:
                details.append(taxpayer)

        return ProviderReport(
            profile=self._merge(tax_id, profiles, details),
            audit_entries=tuple(audit_entries),
        )

    @staticmethod
    def _unpack(
        response: dict[str, Any],
    ) -> tuple[AuditResult, ProviderProfile | None, TaxpayerDetails | None]:
        audit = response.get("audit")
        profile = response.get("profile")
        taxpayer = response.get("taxpayer_details")
        if (
            not isinstance(audit, AuditResult)
            or not (profile is None or isinstance(profile, ProviderProfile))
            or not (taxpayer is None or isinstance(taxpayer, TaxpayerDetails))
        ):
            raise ValueError("Extractor response has invalid 'audit', 'profile' or 'taxpayer_details'")
        return audit, profile, taxpayer

    @staticmethod
    def _merge(
        tax_id: str,
        profiles: list[ProviderProfile],
        details: list[TaxpayerDetails],
    ) -> ProviderProfile:
        taxpayer = next(
            (d for d in (*details, *(p.taxpayer_details for p in profiles)) if d is not None),
            None,
        )
        return ProviderProfile(
            tax_id=tax_id,
            validities=tuple(v for p in profiles for v in p.validities),
            shareholders=tuple(s for p in profiles for s in p.shareholders),
            awards=tuple(a for p in profiles for a in p.awards),
            taxpayer_details=taxpayer,
        )
