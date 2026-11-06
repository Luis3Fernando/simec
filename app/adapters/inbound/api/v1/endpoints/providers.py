import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.dependencies import get_provider_use_case
from app.domain.models.provider import ProviderReport
from app.domain.ports.inbound.get_provider_port import GetProviderPort

logger = logging.getLogger(__name__)

router = APIRouter()

TaxId = Annotated[
    str,
    Path(
        ...,
        pattern=r"^(\d{8}|\d{11})$",
        description="RUC (11 digits) or DNI (8 digits)",
        examples=["20602102344"],
    ),
]


@router.get("/{tax_id}", response_model=ProviderReport, status_code=status.HTTP_200_OK)
async def get_provider(
    tax_id: TaxId,
    use_case: Annotated[GetProviderPort, Depends(get_provider_use_case)],
) -> ProviderReport:
    try:
        return await use_case.get_provider(tax_id)
    except Exception as exc:
        logger.exception("Unexpected error fetching provider %s", tax_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while fetching provider",
        ) from exc
