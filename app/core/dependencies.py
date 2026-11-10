from functools import lru_cache

from app.adapters.outbound.extractors.osce.seace_cda_adapter import SeaceCdaAdapter
from app.adapters.outbound.extractors.taxpayer.apis_net_pe_adapter import ApisNetPeAdapter
from app.adapters.outbound.extractors.sunat.sunat_scraper_adapter import SunatScraperAdapter
from app.application.use_cases.get_provider import GetProviderUseCase
from app.domain.ports.inbound.get_provider_port import GetProviderPort


@lru_cache
def get_provider_use_case() -> GetProviderPort:
    seace_adapter = SeaceCdaAdapter()
    apis_net_pe_adapter = ApisNetPeAdapter()
    sunat_adapter = SunatScraperAdapter()
    return GetProviderUseCase(extractors=[seace_adapter, apis_net_pe_adapter, sunat_adapter])
