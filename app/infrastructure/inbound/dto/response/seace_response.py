from datetime import date

from pydantic import Field

from app.infrastructure.inbound.dto.response.base import ResponseModel
from app.domain.models.seace import ValidityStatus


class RnpValidityResponse(ResponseModel):
    chapter: str = Field(description="Capítulo del RNP", examples=["Proveedor de Bienes"])
    status: ValidityStatus = Field(description="`ACTIVE` si la inscripción está vigente, `INACTIVE` en caso contrario")
    start_date: date | None = Field(description="Fecha de inicio de la inscripción", examples=["2021-03-25"])
    end_date: date | None = Field(description="Fecha de fin. Es `null` cuando la vigencia es indeterminada")
    department: str | None = Field(description="Departamento de la oficina de inscripción", examples=["CUSCO"])


class ShareholderResponse(ResponseModel):
    relationship_type: str = Field(
        description="Relación con la empresa", examples=["ACCIONISTA", "REPRESENTANTE", "ORG. ADMINISTRACION"]
    )
    document_number: str = Field(description="Número de documento de identidad", examples=["44900952"])
    full_name: str = Field(description="Nombre completo o razón social", examples=["RUIZ AUCCAPIÑA RONALD"])
    share_percentage: float = Field(description="Porcentaje de acciones", examples=[100.0])


class AwardRecordResponse(ResponseModel):
    fiscal_year: int = Field(description="Año de la adjudicación", examples=[2023])
    modality: str | None = Field(description="Modalidad de contratación, si la fuente la informa")
    contracting_entity: str = Field(
        description="Entidad pública contratante", examples=["MUNICIPALIDAD PROVINCIAL DE CALCA"]
    )
    amount: float = Field(description="Monto adjudicado en soles (S/)", examples=[322592.71])
    processes_count: int = Field(description="Cantidad de procesos de contratación", examples=[10])


class SeaceProviderRecordResponse(ResponseModel):
    ruc: str = Field(description="RUC del proveedor", examples=["20607524476"])
    validities: list[RnpValidityResponse] = Field(description="Vigencias por capítulo del RNP")
    shareholders: list[ShareholderResponse] = Field(description="Accionistas, administración y representantes")
    awards: list[AwardRecordResponse] = Field(description="Historial de adjudicaciones")


class SeaceProviderPresenceResponse(ResponseModel):
    ruc: str = Field(description="RUC del proveedor vinculado", examples=["20607441414"])
    business_name: str = Field(description="Razón social", examples=["INVERSION DEL SUR DEL PERU S.A.C."])
    condition: str | None = Field(description="Condición general en el RNP", examples=["VIGENTE"])


class SeaceLinkedProviderResponse(ResponseModel):
    presence: SeaceProviderPresenceResponse = Field(description="Presencia de la persona en el RNP")
    record: SeaceProviderRecordResponse = Field(description="Detalle completo del proveedor vinculado")


class SeacePersonRecordResponse(ResponseModel):
    document_number: str = Field(description="DNI consultado", examples=["44900952"])
    linked_providers: list[SeaceLinkedProviderResponse] = Field(
        description="Proveedores donde la persona figura como titular, accionista o representante (máximo 20)"
    )
