from typing import Any

from app.adapters.outbound.extractors.profile.client import ApisNetPeExtractor
from app.adapters.outbound.extractors.shared.extractor import DNI_PATTERN
from app.adapters.outbound.extractors.shared.parsing import optional_text
from app.domain.models.profile import PersonProfile


class ApisNetPeDniAdapter(ApisNetPeExtractor):
    SOURCE_NAME = "APIS_NET_PE_DNI"
    PATTERN = DNI_PATTERN
    PARAMETER_HINT = "an 8-digit DNI"
    ENDPOINT = "dni"

    def _map(self, payload: dict[str, Any], value: str) -> PersonProfile | None:
        full_name = optional_text(payload.get("nombre"))
        if full_name is None:
            return None
        return PersonProfile(
            document_number=optional_text(payload.get("numeroDocumento")) or value,
            full_name=full_name,
            given_names=optional_text(payload.get("nombres")),
            first_surname=optional_text(payload.get("apellidoPaterno")),
            second_surname=optional_text(payload.get("apellidoMaterno")),
            check_digit=optional_text(payload.get("digitoVerificador")),
        )
