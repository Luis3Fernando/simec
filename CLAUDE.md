# Contexto del Proyecto: SIMEC Backend

## 1. Objetivo del Sistema
Backend de alta disponibilidad en FastAPI para el monitoreo de mercados y conductas anticompetitivas. El sistema extrae datos de fuentes públicas peruanas (SEACE, OSCE, SUNAT, prensa), normaliza información de personas naturales y jurídicas, mapea composiciones societarias y contrataciones, y consolida reportes técnicos con auditoría íntegra.

## 2. Patrón de Arquitectura
- **Arquitectura Hexagonal estricta (Puertos y Adaptadores)**.
- **Aislamiento de Dominio:** `app/domain/` no debe importar librerías externas, ni FastAPI, ni HTTPX, ni ORMs.
- **Extractores desacoplados:** Cada fuente externa es un adaptador en `app/adapters/outbound/extractors/` que implementa `ExtractorPort`.
- **Casos de Uso:** Orquestados en `app/application/use_cases/` consumiendo interfaces abstractas mediante inyección de dependencias.
- **Fase actual:** Modo puente/agregador sin base de datos. Se procesan y normalizan los payloads devolviendo JSON estructurado con metadatos de auditoría.

## 3. Estructura del Repositorio
```text
simec-backend/
├── app/
│   ├── domain/                               # Modelos puros y puertos abstractos (ABC)
│   │   ├── models/
│   │   │   └── provider.py                    # RnpValidity, Shareholder, AwardRecord, TaxpayerDetails, SunatProfile, AuditResult, ProviderProfile, ProviderReport
│   │   └── ports/
│   │       ├── inbound/                      # Interfaces de casos de uso (GetProviderPort)
│   │       └── outbound/                     # Contratos de extractores (ExtractorPort)
│   ├── application/
│   │   └── use_cases/                        # GetProviderUseCase (orquesta con asyncio.gather)
│   ├── adapters/
│   │   ├── inbound/
│   │   │   └── api/v1/                       # Routers, endpoints y schemas OpenAPI (GET /api/v1/providers/{tax_id}; Swagger en /docs)
│   │   └── outbound/
│   │       └── extractors/                   # Conectores HTTP/CDA a fuentes públicas
│   │           ├── osce/seace_cda_adapter.py             # SeaceCdaAdapter (SEACE Pentaho CDA)
│   │           ├── taxpayer/apis_net_pe_adapter.py       # ApisNetPeAdapter (apis.net.pe)
│   │           └── sunat/sunat_scraper_adapter.py        # SunatScraperAdapter (SUNAT, Playwright)
│   ├── core/                                 # Configuración y dependencias (get_provider_use_case)
│   └── main.py                               # Entrada FastAPI (rutas bajo /api/v1)
├── notebooks/                                # Laboratorio exploratorio aislado
├── tests/                                    # Pruebas automatizadas (pytest)
├── requirements.txt
└── CLAUDE.md
```

## 4. Fuentes Oficiales Validadas

### SEACE Antecedentes (Pentaho BI CDA)
- **Endpoint:** `https://bi.seace.gob.pe/pentaho/plugin/cda/api/doQuery?userid=public&password=key`
- **Método:** `POST` (`application/x-www-form-urlencoded`).
- **Path CDA:** `/public/ANTECEDENTES_PROVEEDORES/ANTECEDENTES_PROVEEDORES.cda`
- **Consultas activas:**
  - `QUERY_R_F2_new`: Accionistas y representantes legales.
  - `QUERY_R_F3`: Vigencias de inscripción en el Registro Nacional de Proveedores (RNP).
  - `QUERY_R_F5_D_DASH_PROV_RESUMEN`: Historial de órdenes de compra y adjudicaciones.
- **Transformación:** Mapear la matriz `metadata` + `resultset` a diccionarios canónicos tipados.

### apis.net.pe (datos tributarios y de identidad)
- **Base:** `https://api.apis.net.pe/v1`
- **Método:** `GET` con `numero` como query param. Headers: `User-Agent` de navegador, `Accept: application/json`, `Referer: https://apis.net.pe/`.
- **Endpoints:** `/dni` (8 dígitos) y `/ruc` (11 dígitos).
- **Timeout:** 15 s. Las respuestas 404 y 422 se auditan como `NO_DATA`; cualquier otra falla como `ERROR`.
- **Transformación:** Mapear el JSON a `TaxpayerDetails`, expuesto en `ProviderProfile.taxpayer_details`.
- **Contrato del extractor:** `{"audit", "taxpayer_details", "raw"}`.

### SUNAT Consulta RUC (scraping con Playwright)
- **URL:** `https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp`
- **Herramientas:** `playwright.async_api` + `BeautifulSoup`. Usa el navegador instalado (Chrome, luego Edge, luego Chromium de Playwright), viewport 1366x768, locale `es-PE`, `--disable-blink-features=AutomationControlled` y `navigator.webdriver` oculto (técnica del notebook, autorizada por el responsable del proyecto) para pasar la verificación de Cloudflare.
- **Flujo:** Digitar el RUC en `#txtRuc`, buscar con `#btnAceptar` y parsear la ficha desde los `.list-group-item .row`. Representantes legales y establecimientos anexos se obtienen interceptando `HTMLFormElement.prototype.submit` al pulsar cada botón y repitiendo el POST con `fetch` (respuesta decodificada en `iso-8859-1`), sin recargar la página.
- **Limitación:** Si SUNAT igual muestra la verificación de Cloudflare, la ficha se devuelve y la incidencia queda en `details` de la auditoría.
- **Alcance:** Solo RUC de 11 dígitos. Cualquier otro parámetro retorna `NO_DATA` sin abrir el navegador.
- **Timeouts:** 30 s para navegación y por selector. El navegador se cierra siempre en un bloque `finally`.
- **Windows:** Playwright exige `ProactorEventLoop`; si el bucle activo no lo es (p. ej. `uvicorn --reload`), el scraping corre en un hilo con su propio bucle.
- **Contrato del extractor:** `{"audit", "sunat_profile"}`, expuesto en `ProviderProfile.sunat_profile` (incluye `legal_representatives` y `branch_offices`).

---

## 5. Reglas de Código para Claude

- **Nomenclatura en inglés:** Archivos, carpetas, clases, funciones, variables y modelos en inglés técnico. Cero mezcla de idiomas (los nombres de columnas de las fuentes externas se conservan solo al mapearlas).

- **Tipado estricto:** Usar type hints completos (`typing`, `pydantic`).
- **Código conciso:** No incluir comentarios obvios, explicaciones innecesarias ni código de relleno.
- **Manejo de errores:** Las fallas de una fuente no deben romper la ejecución de las demás; registrar incidencias en el bloque de auditoría.
- **SOLID y asincronía:** Métodos asíncronos (`async`/`await`) en operaciones de I/O de red.
- **Sin base de datos por ahora:** No agregar SQLAlchemy, SQLite ni migraciones de Alembic hasta que se indique explícitamente.