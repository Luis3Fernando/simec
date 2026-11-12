from pydantic import ConfigDict, Field

from app.adapters.inbound.docs.examples import COMPANY_EXAMPLE
from app.adapters.inbound.dto.response.audit_response import AuditResultResponse
from app.adapters.inbound.dto.response.base import ResponseModel
from app.adapters.inbound.dto.response.profile_response import CompanyProfileResponse
from app.adapters.inbound.dto.response.rnp_response import RnpRecordResponse
from app.adapters.inbound.dto.response.seace_response import SeaceProviderRecordResponse
from app.adapters.inbound.dto.response.sunat_response import SunatProfileResponse


class CompanyResponse(ResponseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [COMPANY_EXAMPLE]})

    ruc: str = Field(description="RUC consultado", examples=["20607524476"])
    profile: CompanyProfileResponse | None = Field(description="Datos tributarios básicos (apis.net.pe)")
    seace: SeaceProviderRecordResponse | None = Field(
        description="Vigencias RNP, accionistas y adjudicaciones (SEACE)"
    )
    sunat: SunatProfileResponse | None = Field(
        description="Ficha RUC, representantes legales y establecimientos anexos (SUNAT)"
    )
    rnp: RnpRecordResponse | None = Field(description="Inscripciones del Registro Nacional de Proveedores (RNP)")
    audit_entries: list[AuditResultResponse] = Field(
        description="Una entrada de auditoría por fuente. Una fuente caída no bloquea a las demás"
    )
