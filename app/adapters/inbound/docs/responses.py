from typing import Any, Final

from fastapi import status

from app.adapters.inbound.dto.response.error_response import ErrorResponse

COMPANY_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_200_OK: {
        "description": "Reporte generado. Revise `audit_entries` para ver el estado de cada fuente."
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "`ruc` no tiene exactamente 11 dígitos."},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "description": "Error inesperado al generar el reporte.",
    },
}

PERSON_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_200_OK: {
        "description": "Reporte generado. Revise `audit_entries` para ver el estado de cada fuente."
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "`dni` no tiene exactamente 8 dígitos."},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "description": "Error inesperado al generar el reporte.",
    },
}
