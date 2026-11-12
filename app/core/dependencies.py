from functools import lru_cache

from app.adapters.outbound.extractors.profile.dni_adapter import ApisNetPeDniAdapter
from app.adapters.outbound.extractors.profile.ruc_adapter import ApisNetPeRucAdapter
from app.adapters.outbound.extractors.rnp.ruc_adapter import RnpRucAdapter
from app.adapters.outbound.extractors.seace.dni_adapter import SeaceDniAdapter
from app.adapters.outbound.extractors.seace.ruc_adapter import SeaceRucAdapter
from app.adapters.outbound.extractors.sunat.dni_adapter import SunatDniAdapter
from app.adapters.outbound.extractors.sunat.ruc_adapter import SunatRucAdapter
from app.application.port.usecase.get_company_use_case import GetCompanyUseCase
from app.application.port.usecase.get_person_use_case import GetPersonUseCase
from app.application.services.get_company_service import GetCompanyService
from app.application.services.get_person_service import GetPersonService


@lru_cache
def get_company_use_case() -> GetCompanyUseCase:
    return GetCompanyService(
        profile=ApisNetPeRucAdapter(),
        seace=SeaceRucAdapter(),
        sunat=SunatRucAdapter(),
        rnp=RnpRucAdapter(),
    )


@lru_cache
def get_person_use_case() -> GetPersonUseCase:
    return GetPersonService(
        profile=ApisNetPeDniAdapter(),
        seace=SeaceDniAdapter(),
        sunat=SunatDniAdapter(),
    )
