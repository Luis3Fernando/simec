from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.inbound.api.v1.router import api_router

DESCRIPTION = """
Backend para el monitoreo de mercados y conductas anticompetitivas.

Agrega fuentes públicas peruanas (**SEACE**, **SUNAT**, **apis.net.pe**), normaliza la
información de personas naturales y jurídicas, y devuelve un reporte consolidado con
auditoría por fuente.

* Sin base de datos: cada consulta se resuelve en vivo contra las fuentes.
* Cada fuente queda auditada con duración, estado y detalle.
"""

TAGS_METADATA = [
    {
        "name": "Providers",
        "description": "Reportes consolidados de proveedores por **RUC** (11 dígitos) o **DNI** (8 dígitos).",
    }
]

app = FastAPI(
    title="SIMEC Backend",
    version="0.1.0",
    summary="API de monitoreo de proveedores y mercados",
    description=DESCRIPTION,
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
