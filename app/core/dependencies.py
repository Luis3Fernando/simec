from functools import lru_cache

from app.adapters.outbound.extractors.osce.seace_cda_adapter import SeaceCdaAdapter
from app.application.use_cases.get_provider import GetProviderUseCase
from app.domain.ports.inbound.get_provider_port import GetProviderPort


@lru_cache
def get_provider_use_case() -> GetProviderPort:
    return GetProviderUseCase(extractors=[SeaceCdaAdapter()])
