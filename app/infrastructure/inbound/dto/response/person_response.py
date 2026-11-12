from pydantic import ConfigDict, Field

from app.infrastructure.inbound.docs.examples import PERSON_EXAMPLE
from app.infrastructure.inbound.dto.response.audit_response import AuditResultResponse
from app.infrastructure.inbound.dto.response.base import ResponseModel
from app.infrastructure.inbound.dto.response.profile_response import PersonProfileResponse
from app.infrastructure.inbound.dto.response.seace_response import SeacePersonRecordResponse
from app.infrastructure.inbound.dto.response.sunat_response import SunatProfileResponse


class PersonResponse(ResponseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [PERSON_EXAMPLE]})

    dni: str = Field(description="DNI consultado", examples=["44900952"])
    profile: PersonProfileResponse | None = Field(description="Identidad de la persona (apis.net.pe)")
    seace: SeacePersonRecordResponse | None = Field(
        description="Proveedores vinculados a la persona y su detalle (SEACE)"
    )
    sunat: SunatProfileResponse | None = Field(
        description="Ficha del RUC de la persona natural en SUNAT, si tiene uno"
    )
    audit_entries: list[AuditResultResponse] = Field(
        description="Una entrada de auditoría por fuente. Una fuente caída no bloquea a las demás"
    )
