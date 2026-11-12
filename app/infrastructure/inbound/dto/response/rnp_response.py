from datetime import date

from pydantic import Field

from app.infrastructure.inbound.dto.response.base import ResponseModel


class RnpRegistrationResponse(ResponseModel):
    chapter: str = Field(description="Capítulo de la inscripción", examples=["BIENES", "SERVICIOS"])
    provider_code: str | None = Field(description="Código de proveedor asignado")
    payment_date: date | None = Field(description="Fecha de pago de la tasa", examples=["2021-03-18"])
    procedure_number: str | None = Field(description="Número de trámite o cargo", examples=["2021-18895585"])
    status: str | None = Field(description="Estado de la inscripción", examples=["APROBACION AUTOMATICA"])
    reason: str | None = Field(description="Motivo del estado", examples=["REQUISITOS CONFORME"])


class RnpRecordResponse(ResponseModel):
    ruc: str = Field(description="RUC consultado", examples=["20607524476"])
    business_name: str | None = Field(description="Razón social registrada en el RNP")
    registrations: list[RnpRegistrationResponse] = Field(description="Historial de inscripciones por capítulo")
