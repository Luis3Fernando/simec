import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Final, NamedTuple

from app.domain.models.provider import (
    AuditResult,
    AuditStatus,
    ProviderProfile,
    ProviderReport,
    SunatProfile,
    TaxpayerDetails,
)
from app.domain.ports.inbound.get_provider_port import GetProviderPort
from app.domain.ports.outbound.extractor_port import ExtractorPort

DEFAULT_TIMEOUT_S: Final = 120.0


class Extraction(NamedTuple):
    audit: AuditResult
    profile: ProviderProfile | None
    taxpayer_details: TaxpayerDetails | None
    sunat_profile: SunatProfile | None


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

        extractions: list[Extraction] = []
        audit_entries: list[AuditResult] = []
        for extractor, response in zip(self._extractors, responses):
            try:
                if isinstance(response, BaseException):
                    raise response
                extraction = self._unpack(response)
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
            audit_entries.append(extraction.audit)
            extractions.append(extraction)

        return ProviderReport(
            profile=self._merge(tax_id, extractions),
            audit_entries=tuple(audit_entries),
        )

    @staticmethod
    def _unpack(response: dict[str, Any]) -> Extraction:
        extraction = Extraction(
            audit=response.get("audit"),
            profile=response.get("profile"),
            taxpayer_details=response.get("taxpayer_details"),
            sunat_profile=response.get("sunat_profile"),
        )
        expected: tuple[tuple[Any, type], ...] = (
            (extraction.profile, ProviderProfile),
            (extraction.taxpayer_details, TaxpayerDetails),
            (extraction.sunat_profile, SunatProfile),
        )
        if not isinstance(extraction.audit, AuditResult) or any(
            value is not None and not isinstance(value, kind) for value, kind in expected
        ):
            raise ValueError("Extractor response has invalid 'audit' or profile payloads")
        return extraction

    @staticmethod
    def _merge(tax_id: str, extractions: list[Extraction]) -> ProviderProfile:
        profiles = [e.profile for e in extractions if e.profile is not None]
        taxpayer = next(
            (
                d
                for d in (
                    *(e.taxpayer_details for e in extractions),
                    *(p.taxpayer_details for p in profiles),
                )
                if d is not None
            ),
            None,
        )
        sunat = next(
            (
                s
                for s in (
                    *(e.sunat_profile for e in extractions),
                    *(p.sunat_profile for p in profiles),
                )
                if s is not None
            ),
            None,
        )
        return ProviderProfile(
            tax_id=tax_id,
            validities=tuple(v for p in profiles for v in p.validities),
            shareholders=tuple(s for p in profiles for s in p.shareholders),
            awards=tuple(a for p in profiles for a in p.awards),
            taxpayer_details=taxpayer,
            sunat_profile=sunat,
        )
