import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.inbound.docs.responses import PERSON_RESPONSES
from app.adapters.inbound.dto.request.person_request import DniPathParam
from app.adapters.inbound.dto.response.person_response import PersonResponse
from app.adapters.inbound.mapper import person_mapper
from app.application.port.usecase.get_person_use_case import GetPersonUseCase
from app.core.dependencies import get_person_use_case

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{dni}",
    operation_id="get_person",
    summary="Consultar una persona por DNI",
    description=(
        "Consulta en paralelo todas las fuentes disponibles para un DNI y devuelve un reporte "
        "consolidado.\n\n"
        "- **apis.net.pe:** identidad de la persona (nombres y apellidos).\n"
        "- **SEACE:** proveedores donde la persona figura como titular, accionista o representante, "
        "con el detalle de cada uno.\n"
        "- **SUNAT:** ficha del RUC de la persona natural, si tiene uno.\n\n"
        "El RNP no admite consultas por DNI. Una fuente caída o lenta no bloquea a las demás: su "
        "resultado queda en `audit_entries` con estado `ERROR` o `NO_DATA`, y el resto se devuelve igual."
    ),
    response_model=PersonResponse,
    status_code=status.HTTP_200_OK,
    responses=PERSON_RESPONSES,
)
async def get_person(
    dni: DniPathParam,
    use_case: Annotated[GetPersonUseCase, Depends(get_person_use_case)],
) -> PersonResponse:
    try:
        result = await use_case.execute(person_mapper.to_command(dni))
    except Exception as exc:
        logger.exception("Unexpected error fetching person %s", dni)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while fetching person",
        ) from exc
    return person_mapper.to_response(result)
