from datetime import date

from pydantic import Field

from app.adapters.inbound.dto.response.base import ResponseModel


class LegalRepresentativeResponse(ResponseModel):
    document_type: str = Field(description="Tipo de documento", examples=["DNI"])
    document_number: str = Field(description="Número de documento", examples=["44900952"])
    full_name: str = Field(description="Nombre completo", examples=["RUIZ AUCCAPIÑA RONALD"])
    role: str = Field(description="Cargo", examples=["TITULAR-GERENTE"])
    start_date: date | None = Field(description="Fecha desde la que ejerce el cargo", examples=["2021-02-08"])


class BranchOfficeResponse(ResponseModel):
    code: str = Field(description="Código del establecimiento", examples=["0004"])
    establishment_type: str = Field(description="Tipo de establecimiento", examples=["DE. DEPOSITO"])
    address: str = Field(description="Dirección del establecimiento")
    economic_activity: str = Field(description="Código CIIU de la actividad", examples=["4630"])


class SunatProfileResponse(ResponseModel):
    tax_id: str = Field(description="RUC de la ficha. Para un DNI, es el RUC de la persona natural", examples=["20607524476"])
    taxpayer_type: str | None = Field(description="Tipo de contribuyente", examples=["EMPRESA INDIVIDUAL DE RESP. LTDA"])
    commercial_name: str | None = Field(description="Nombre comercial")
    registration_date: date | None = Field(description="Fecha de inscripción", examples=["2021-02-24"])
    activity_start_date: date | None = Field(description="Fecha de inicio de actividades", examples=["2021-03-15"])
    status: str | None = Field(description="Estado del contribuyente", examples=["ACTIVO"])
    condition: str | None = Field(description="Condición del contribuyente", examples=["HABIDO"])
    tax_alert: str | None = Field(description="Alerta tributaria publicada por SUNAT, si existe")
    fiscal_address: str | None = Field(description="Domicilio fiscal")
    economic_activities: list[str] = Field(
        description="Actividades económicas, principal y secundarias",
        examples=[["Principal - 4630 - VENTA AL POR MAYOR DE ALIMENTOS, BEBIDAS Y TABACO"]],
    )
    electronic_issuance: str | None = Field(
        description="Sistema de emisión electrónica", examples=["FACTURA PORTAL DESDE 27/05/2021"]
    )
    legal_representatives: list[LegalRepresentativeResponse] = Field(description="Representantes legales")
    branch_offices: list[BranchOfficeResponse] = Field(
        description="Establecimientos anexos. Vacío si el RUC no tiene anexos"
    )
