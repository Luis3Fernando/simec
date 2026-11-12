import asyncio
from typing import Any, Final

import httpx

from app.adapters.outbound.extractors.seace.mappers import (
    matrix_to_rows,
    to_award,
    to_shareholder,
    to_validity,
)
from app.domain.models.seace import SeaceProviderRecord

CDA_URL: Final = "https://bi.seace.gob.pe/pentaho/plugin/cda/api/doQuery?userid=public&password=key"
CDA_PATH: Final = "/public/ANTECEDENTES_PROVEEDORES/ANTECEDENTES_PROVEEDORES.cda"
TIMEOUT_S: Final = 25.0
HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://bi.seace.gob.pe",
    "Referer": (
        "https://bi.seace.gob.pe/pentaho/api/repos/:public:ANTECEDENTES_PROVEEDORES:"
        "ANTECEDENTES_PROVEEDORES.wcdf/generatedContent?userid=public&password=key"
    ),
}
PRESENCE_QUERY: Final = "QUERY_R_F0"
DETAIL_QUERIES: Final = {
    "shareholders": "QUERY_R_F2_new",
    "validities": "QUERY_R_F3",
    "awards": "QUERY_R_F5_D_DASH_PROV_RESUMEN",
}


def open_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT_S)


async def query_cda(client: httpx.AsyncClient, query_id: str, **params: str) -> dict[str, Any]:
    response = await client.post(
        CDA_URL,
        data={
            "path": CDA_PATH,
            "dataAccessId": query_id,
            "outputIndexId": "1",
            "pageSize": "0",
            "pageStart": "0",
            "paramsearchBox": "",
            **params,
        },
    )
    response.raise_for_status()
    return response.json()


async def fetch_provider_record(
    client: httpx.AsyncClient, ruc: str
) -> tuple[SeaceProviderRecord, dict[str, dict[str, Any] | None], list[str]]:
    responses = await asyncio.gather(
        *(query_cda(client, query_id, paramPARAM_RUC=ruc) for query_id in DETAIL_QUERIES.values()),
        return_exceptions=True,
    )
    raw: dict[str, dict[str, Any] | None] = {}
    errors: list[str] = []
    for key, response in zip(DETAIL_QUERIES, responses):
        if isinstance(response, BaseException):
            raw[key] = None
            errors.append(f"{DETAIL_QUERIES[key]}: {type(response).__name__}: {response}")
        else:
            raw[key] = response

    record = SeaceProviderRecord(
        ruc=ruc,
        validities=tuple(to_validity(r) for r in matrix_to_rows(raw["validities"])),
        shareholders=tuple(to_shareholder(r) for r in matrix_to_rows(raw["shareholders"])),
        awards=tuple(to_award(r) for r in matrix_to_rows(raw["awards"])),
    )
    return record, raw, errors
