from datetime import datetime

from pydantic import Field

from app.infrastructure.inbound.dto.response.base import ResponseModel
from app.domain.models.audit import AuditStatus


class AuditResultResponse(ResponseModel):
    source_name: str = Field(description="Fuente que generó esta entrada", examples=["SEACE_PENTAHO_CDA_RUC"])
    query_parameter: str = Field(description="Parámetro enviado a la fuente", examples=["20607524476"])
    duration_ms: int = Field(description="Duración de la consulta en milisegundos", examples=[779])
    status: AuditStatus = Field(
        description="`SUCCESS` si la fuente devolvió datos, `NO_DATA` si no hay información y `ERROR` si falló"
    )
    details: str | None = Field(description="Detalle del fallo o de los datos parciales, si aplica")
    executed_at_utc: datetime = Field(description="Fecha y hora de la consulta (UTC)")
