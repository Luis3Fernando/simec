from typing import Any

from app.infrastructure.outbound.extractors.profile.client import ApisNetPeExtractor
from app.infrastructure.outbound.extractors.shared.extractor import RUC_PATTERN
from app.infrastructure.outbound.extractors.shared.parsing import optional_text
from app.domain.models.profile import CompanyProfile


class ApisNetPeRucAdapter(ApisNetPeExtractor):
    SOURCE_NAME = "APIS_NET_PE_RUC"
    PATTERN = RUC_PATTERN
    PARAMETER_HINT = "an 11-digit RUC"
    ENDPOINT = "ruc"

    def _map(self, payload: dict[str, Any], value: str) -> CompanyProfile | None:
        legal_name = optional_text(payload.get("nombre"))
        if legal_name is None:
            return None
        return CompanyProfile(
            document_number=optional_text(payload.get("numeroDocumento")) or value,
            legal_name=legal_name,
            status=optional_text(payload.get("estado")),
            condition=optional_text(payload.get("condicion")),
            address=optional_text(payload.get("direccion")),
            ubigeo=optional_text(payload.get("ubigeo")),
            department=optional_text(payload.get("departamento")),
            province=optional_text(payload.get("provincia")),
            district=optional_text(payload.get("distrito")),
            via_type=optional_text(payload.get("viaTipo")),
            via_name=optional_text(payload.get("viaNombre")),
            zone_type=optional_text(payload.get("zonaTipo")),
            zone_code=optional_text(payload.get("zonaCodigo")),
            number=optional_text(payload.get("numero")),
            lot=optional_text(payload.get("lote")),
            apartment=optional_text(payload.get("dpto")),
            block=optional_text(payload.get("manzana")),
            kilometer=optional_text(payload.get("kilometro")),
        )
