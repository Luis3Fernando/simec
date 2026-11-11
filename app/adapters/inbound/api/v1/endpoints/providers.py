import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.adapters.inbound.api.v1.schemas import ErrorResponse, ProviderReportResponse
from app.core.dependencies import get_provider_use_case
from app.domain.ports.inbound.get_provider_port import GetProviderPort

logger = logging.getLogger(__name__)

router = APIRouter()

TaxId = Annotated[
    str,
    Path(
        pattern=r"^(\d{8}|\d{11})$",
        description="RUC (11 dígitos) o DNI (8 dígitos).",
        examples=["20602102344"],
    ),
]


@router.get(
    "/{tax_id}",
    operation_id="get_provider",
    summary="Obtener el reporte consolidado de un proveedor",
    description=(
        "Consulta todas las fuentes registradas de forma concurrente y unifica los resultados "
        "en un solo perfil.\n\n"
        "- **SEACE (Pentaho CDA):** inscripciones en el RNP, accionistas e historial de "
        "adjudicaciones. Solo RUC.\n"
        "- **apis.net.pe:** datos tributarios y de identidad de un DNI o RUC.\n"
        "- **SUNAT:** ficha RUC, representantes legales y establecimientos anexos. Solo RUC.\n\n"
        "Una fuente caída o lenta no bloquea a las demás: su resultado queda en `audit_entries` "
        "con estado `ERROR` o `NO_DATA`, y las otras fuentes se devuelven igual."
    ),
    response_model=ProviderReportResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Reporte generado. Revise `audit_entries` para ver el estado de cada fuente."
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "`tax_id` no es un DNI de 8 dígitos ni un RUC de 11 dígitos."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Error inesperado al generar el reporte.",
        },
    },
)
async def get_provider(
    tax_id: TaxId,
    use_case: Annotated[GetProviderPort, Depends(get_provider_use_case)],
) -> ProviderReportResponse:
    try:
        report = await use_case.get_provider(tax_id)
    except Exception as exc:
        logger.exception("Unexpected error fetching provider %s", tax_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while fetching provider",
        ) from exc
    return ProviderReportResponse.model_validate(report)
