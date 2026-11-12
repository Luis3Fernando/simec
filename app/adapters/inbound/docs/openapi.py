from typing import Any, Final

DESCRIPTION: Final = """
Backend para el monitoreo de mercados y conductas anticompetitivas.

Agrega fuentes públicas peruanas (**SEACE**, **SUNAT**, **RNP** y **apis.net.pe**), normaliza la
información de personas naturales y jurídicas, y devuelve un reporte consolidado con
auditoría por fuente.

* Dos consultas independientes: por **RUC** (empresas) y por **DNI** (personas).
* Sin base de datos: cada consulta se resuelve en vivo contra las fuentes.
* Cada fuente queda auditada con duración, estado y detalle. Una fuente caída no bloquea a las demás.
"""

TAGS_METADATA: Final[list[dict[str, Any]]] = [
    {
        "name": "Companies",
        "description": (
            "Consulta por **RUC** (11 dígitos). Fuentes: apis.net.pe, SEACE, SUNAT y RNP."
        ),
    },
    {
        "name": "Persons",
        "description": (
            "Consulta por **DNI** (8 dígitos). Fuentes: apis.net.pe, SEACE y SUNAT. "
            "El RNP no admite consultas por DNI."
        ),
    },
]

API_METADATA: Final[dict[str, Any]] = {
    "title": "SIMEC Backend",
    "version": "0.1.0",
    "summary": "API de monitoreo de proveedores y mercados",
    "description": DESCRIPTION,
    "openapi_tags": TAGS_METADATA,
}
