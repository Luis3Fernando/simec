from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.provider import AuditStatus, ValidityStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RnpValidityResponse(ORMModel):
    chapter: str = Field(description="Capítulo del RNP", examples=["Proveedor de Bienes"])
    status: ValidityStatus = Field(description="Estado de la inscripción en el RNP")
    start_date: date | None = Field(description="Fecha de inicio de la inscripción", examples=["2018-06-07"])
    end_date: date | None = Field(description="Fecha de fin de la inscripción", examples=["2025-06-13"])
    department: str | None = Field(description="Departamento de la oficina de inscripción", examples=["CUSCO"])


class ShareholderResponse(ORMModel):
    relationship_type: str = Field(
        description="Relación con la empresa", examples=["ACCIONISTA", "REPRESENTANTE"]
    )
    document_number: str = Field(description="Número de documento de identidad", examples=["43453374"])
    full_name: str = Field(description="Nombre completo o razón social", examples=["RUIZ AUCCAPIÑA ELISBAN"])
    share_percentage: float = Field(description="Porcentaje de acciones", examples=[100.0])


class AwardRecordResponse(ORMModel):
    fiscal_year: int = Field(description="Año de la adjudicación", examples=[2024])
    modality: str | None = Field(description="Modalidad de la adjudicación, si la fuente la informa")
    contracting_entity: str = Field(
        description="Entidad pública contratante", examples=["MUNICIPALIDAD DISTRITAL DE WANCHAQ"]
    )
    amount: float = Field(description="Monto adjudicado en soles (S/)", examples=[229054.0])
    processes_count: int = Field(description="Cantidad de procesos de contratación", examples=[5])


class TaxpayerDetailsResponse(ORMModel):
    document_type: str = Field(description="Tipo de documento", examples=["DNI", "RUC"])
    document_number: str = Field(description="Número de documento", examples=["20602102344"])
    legal_name: str = Field(description="Razón social o nombre completo")
    tax_status: str | None = Field(description="Estado del contribuyente", examples=["ACTIVO"])
    tax_condition: str | None = Field(description="Condición del contribuyente", examples=["HABIDO"])
    fiscal_address: str | None = Field(description="Domicilio fiscal")
    ubigeo: str | None = Field(description="Código de ubigeo del INEI", examples=["080101"])
    department: str | None = Field(description="Departamento", examples=["CUSCO"])
    province: str | None = Field(description="Provincia", examples=["CUSCO"])
    district: str | None = Field(description="Distrito", examples=["SAN JERONIMO"])
    first_surname: str | None = Field(description="Apellido paterno (solo personas naturales)")
    second_surname: str | None = Field(description="Apellido materno (solo personas naturales)")
    given_names: str | None = Field(description="Nombres (solo personas naturales)")


class SunatProfileResponse(ORMModel):
    tax_id: str = Field(description="RUC consultado", examples=["20602102344"])
    taxpayer_type: str | None = Field(
        description="Tipo de contribuyente", examples=["EMPRESA INDIVIDUAL DE RESP. LTDA"]
    )
    commercial_name: str | None = Field(description="Nombre comercial")
    registration_date: str | None = Field(description="Fecha de inscripción (dd/mm/aaaa)", examples=["06/05/2017"])
    activity_start_date: str | None = Field(
        description="Fecha de inicio de actividades (dd/mm/aaaa)", examples=["15/06/2017"]
    )
    status: str | None = Field(description="Estado del contribuyente", examples=["SUSPENSION TEMPORAL"])
    condition: str | None = Field(description="Condición del contribuyente", examples=["HABIDO"])
    fiscal_address: str | None = Field(description="Domicilio fiscal")
    economic_activities: list[str] = Field(
        description="Actividades económicas (principal y secundarias)",
        examples=[["Principal - 4630 - VENTA AL POR MAYOR DE ALIMENTOS, BEBIDAS Y TABACO"]],
    )
    electronic_issuance: str | None = Field(
        description="Sistema de emisión electrónica", examples=["FACTURA PORTAL DESDE 16/11/2018"]
    )
    legal_representatives: list[dict[str, Any]] = Field(
        description="Representantes legales: document_type, document_number, full_name, role, start_date"
    )
    branch_offices: list[dict[str, Any]] = Field(
        description="Establecimientos anexos: code, establishment_type, address, economic_activity"
    )


class ProviderProfileResponse(ORMModel):
    tax_id: str = Field(description="RUC o DNI consultado", examples=["20602102344"])
    validities: list[RnpValidityResponse] = Field(description="Inscripciones en el RNP (SEACE)")
    shareholders: list[ShareholderResponse] = Field(description="Accionistas y representantes (SEACE)")
    awards: list[AwardRecordResponse] = Field(description="Historial de adjudicaciones (SEACE)")
    taxpayer_details: TaxpayerDetailsResponse | None = Field(
        description="Datos tributarios y de identidad (apis.net.pe)"
    )
    sunat_profile: SunatProfileResponse | None = Field(
        description="Ficha RUC de SUNAT, representantes legales y establecimientos anexos"
    )


class AuditResultResponse(ORMModel):
    source_name: str = Field(description="Fuente que generó esta entrada", examples=["SEACE_PENTAHO_CDA"])
    query_parameter: str = Field(description="Parámetro enviado a la fuente", examples=["20602102344"])
    duration_ms: int = Field(description="Duración de la consulta en milisegundos", examples=[779])
    status: AuditStatus = Field(description="Resultado de la consulta a la fuente")
    details: str | None = Field(description="Detalle del fallo o de los datos parciales, si aplica")
    executed_at_utc: datetime = Field(description="Fecha y hora de la consulta (UTC)")


class ProviderReportResponse(ORMModel):
    profile: ProviderProfileResponse = Field(description="Datos consolidados de todas las fuentes")
    audit_entries: list[AuditResultResponse] = Field(
        description="Una entrada de auditoría por fuente. Una fuente caída no bloquea a las demás"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "profile": {
                    "tax_id": "20602102344",
                    "validities": [
                        {
                            "chapter": "Proveedor de Bienes",
                            "status": "INACTIVE",
                            "start_date": "2018-06-07",
                            "end_date": "2025-06-13",
                            "department": "CUSCO",
                        }
                    ],
                    "shareholders": [
                        {
                            "relationship_type": "ACCIONISTA",
                            "document_number": "43453374",
                            "full_name": "RUIZ AUCCAPIÑA ELISBAN",
                            "share_percentage": 100.0,
                        }
                    ],
                    "awards": [
                        {
                            "fiscal_year": 2024,
                            "modality": None,
                            "contracting_entity": "MUNICIPALIDAD DISTRITAL DE WANCHAQ",
                            "amount": 229054.0,
                            "processes_count": 5,
                        }
                    ],
                    "taxpayer_details": None,
                    "sunat_profile": None,
                },
                "audit_entries": [
                    {
                        "source_name": "SEACE_PENTAHO_CDA",
                        "query_parameter": "20602102344",
                        "duration_ms": 779,
                        "status": "SUCCESS",
                        "details": None,
                        "executed_at_utc": "2026-11-10T14:49:46.322370Z",
                    }
                ],
            }
        },
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        description="Descripción del error", examples=["Internal error while fetching provider"]
    )
