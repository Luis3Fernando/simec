from app.adapters.outbound.extractors.seace.cda_client import fetch_provider_record, open_client
from app.adapters.outbound.extractors.shared.extractor import RUC_PATTERN, BaseExtractor, Outcome


class SeaceRucAdapter(BaseExtractor):
    SOURCE_NAME = "SEACE_PENTAHO_CDA_RUC"
    PATTERN = RUC_PATTERN
    PARAMETER_HINT = "an 11-digit RUC"

    async def _fetch(self, value: str) -> Outcome:
        async with open_client() as client:
            record, raw, errors = await fetch_provider_record(client, value)
        has_data = bool(record.validities or record.shareholders or record.awards)
        return Outcome(
            data=record if has_data else None,
            raw=raw,
            details="; ".join(errors) or None,
            failed=bool(errors),
        )
