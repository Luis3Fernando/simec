import asyncio
from typing import Any, Final

from app.infrastructure.outbound.extractors.seace.cda_client import (
    PRESENCE_QUERY,
    fetch_provider_record,
    open_client,
    query_cda,
)
from app.infrastructure.outbound.extractors.seace.mappers import matrix_to_rows, to_presence
from app.infrastructure.outbound.extractors.shared.extractor import DNI_PATTERN, BaseExtractor, Outcome
from app.domain.models.seace import SeaceLinkedProvider, SeacePersonRecord

MAX_LINKED_PROVIDERS: Final = 20
MAX_CONCURRENT_PROVIDERS: Final = 5


class SeaceDniAdapter(BaseExtractor):
    SOURCE_NAME = "SEACE_PENTAHO_CDA_DNI"
    PATTERN = DNI_PATTERN
    PARAMETER_HINT = "an 8-digit DNI"

    async def _fetch(self, value: str) -> Outcome:
        async with open_client() as client:
            presence_payload = await query_cda(client, PRESENCE_QUERY, paramPARAM_DNIRUC0=value)
            presences = [
                p for row in matrix_to_rows(presence_payload) if (p := to_presence(row)) is not None
            ][:MAX_LINKED_PROVIDERS]
            if not presences:
                return Outcome(raw={"presence": presence_payload})

            semaphore = asyncio.Semaphore(MAX_CONCURRENT_PROVIDERS)

            async def fetch_one(ruc: str) -> Any:
                async with semaphore:
                    return await fetch_provider_record(client, ruc)

            results = await asyncio.gather(*(fetch_one(p.ruc) for p in presences))

        errors = [f"{p.ruc}: {e}" for p, (_, _, errs) in zip(presences, results) for e in errs]
        record = SeacePersonRecord(
            document_number=value,
            linked_providers=tuple(
                SeaceLinkedProvider(presence=p, record=r)
                for p, (r, _, _) in zip(presences, results)
            ),
        )
        raw = {
            "presence": presence_payload,
            "providers": {p.ruc: provider_raw for p, (_, provider_raw, _) in zip(presences, results)},
        }
        return Outcome(data=record, raw=raw, details="; ".join(errors) or None)
