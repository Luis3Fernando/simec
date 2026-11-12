# Contexto del Proyecto: SIMEC Backend

## 1. Objetivo del Sistema
Backend de alta disponibilidad en FastAPI para el monitoreo de mercados y conductas anticompetitivas. El sistema extrae datos de fuentes públicas peruanas (SEACE, OSCE, SUNAT, prensa), normaliza información de personas naturales y jurídicas, mapea composiciones societarias y contrataciones, y consolida reportes técnicos con auditoría íntegra.

## 2. Patrón de Arquitectura
- **Arquitectura Hexagonal estricta (Puertos y Adaptadores)**.
- **Aislamiento de Dominio:** `app/domain/` solo contiene entidades y no debe importar librerías externas, ni FastAPI, ni HTTPX, ni ORMs.
- **Infraestructura:** `app/infrastructure/` contiene los adaptadores: `inbound/` (HTTP) y `outbound/` (fuentes externas).
- **Extractores desacoplados:** Cada fuente externa es un adaptador en `app/infrastructure/outbound/extractors/` que implementa `ExtractorPort` (`app/application/port/out/`).
- **Casos de Uso:** Cada caso de uso es una interfaz en `app/application/port/usecase/` (nombre `*_use_case.py`, método `execute(command) -> result`) y su implementación vive en `app/application/services/` (`*_service.py`). Reciben `Command` y devuelven `Result` (`app/application/dto/`). Los puertos de salida están en `app/application/port/out/`. Todo lo que no sea un caso de uso va fuera de su carpeta.
- **Fase actual:** Modo puente/agregador sin base de datos. Se procesan y normalizan los payloads devolviendo JSON estructurado con metadatos de auditoría.

## 3. Estructura del Repositorio
```text
simec-backend/
├── app/
│   ├── domain/                               # Entidades puras, sin dependencias externas
│   │   └── models/
│   │       ├── audit.py                      # AuditResult, AuditStatus (comunes a todas las fuentes)
│   │       ├── profile.py                    # apis.net.pe: PersonProfile (DNI), CompanyProfile (RUC)
│   │       ├── seace.py                      # SEACE: RnpValidity, Shareholder, AwardRecord, SeaceProviderRecord, SeacePersonRecord
│   │       ├── sunat.py                      # SUNAT: SunatProfile, LegalRepresentative, BranchOffice
│   │       └── rnp.py                        # RNP (solo RUC): RnpRecord, RnpRegistration
│   ├── application/
│   │   ├── dto/
│   │   │   ├── command/                      # Entradas: GetCompanyCommand (RUC), GetPersonCommand (DNI)
│   │   │   └── result/                       # Salidas: CompanyResult (RUC), PersonResult (DNI)
│   │   ├── port/
│   │   │   ├── usecase/                      # Puertos de entrada: GetCompanyUseCase, GetPersonUseCase (execute)
│   │   │   └── out/                          # Puertos de salida: ExtractorPort
│   │   └── services/                         # Implementan los casos de uso: GetCompanyService, GetPersonService (+ source_runner.py)
│   ├── infrastructure/
│   │   ├── inbound/                          # Adaptador HTTP (FastAPI)
│   │   │   ├── controller/v1/                # company_controller.py (GET /api/v1/companies/{ruc}), person_controller.py (GET /api/v1/persons/{dni}), router.py
│   │   │   ├── dto/
│   │   │   │   ├── request/                  # Parámetros de entrada validados (RucPathParam, DniPathParam)
│   │   │   │   └── response/                 # Modelos Pydantic de respuesta por fuente, CompanyResponse, PersonResponse, ErrorResponse
│   │   │   ├── mapper/                       # Command <-> Result <-> Response (company_mapper.py, person_mapper.py)
│   │   │   └── docs/                         # OpenAPI: metadatos y tags (openapi.py), respuestas (responses.py), ejemplos (examples.py)
│   │   └── outbound/
│   │       └── extractors/                   # Conectores HTTP/CDA a fuentes públicas
│   │           ├── shared/                       # BaseExtractor, parsing y navegador Playwright compartidos
│   │           ├── profile/                      # apis.net.pe: ruc_adapter.py, dni_adapter.py
│   │           ├── seace/                        # SEACE Pentaho CDA: ruc_adapter.py, dni_adapter.py
│   │           ├── sunat/                        # SUNAT (Playwright): ruc_adapter.py, dni_adapter.py
│   │           └── rnp/                          # RNP (solo RUC): ruc_adapter.py
│   ├── core/                                 # Configuración y dependencias (get_company_use_case, get_person_use_case)
│   └── main.py                               # Entrada FastAPI (rutas bajo /api/v1; Swagger en /docs y ReDoc en /redoc)
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
- **Transformación:** Mapear la matriz `metadata` + `resultset` a modelos tipados.
- **Por DNI:** `QUERY_R_F0` (`paramPARAM_DNIRUC0`) lista los RUC vinculados (máximo 20, 5 en paralelo) y se consultan las 3 consultas de detalle por cada uno (`SeaceDniAdapter` → `SeacePersonRecord`). Por RUC: `SeaceRucAdapter` → `SeaceProviderRecord`.
- **Contrato del extractor:** `{"audit", "data", "raw"}`.

### apis.net.pe (datos tributarios y de identidad)
- **Base:** `https://api.apis.net.pe/v1`
- **Método:** `GET` con `numero` como query param. Headers: `User-Agent` de navegador, `Accept: application/json`, `Referer: https://apis.net.pe/`.
- **Endpoints:** `/dni` (8 dígitos) y `/ruc` (11 dígitos).
- **Timeout:** 15 s. Las respuestas 404 y 422 se auditan como `NO_DATA`; cualquier otra falla como `ERROR`.
- **Transformación:** Mapear el JSON a `CompanyProfile` (`ApisNetPeRucAdapter`) o `PersonProfile` (`ApisNetPeDniAdapter`).
- **Contrato del extractor:** `{"audit", "data", "raw"}` con `data` como `CompanyProfile` (RUC) o `PersonProfile` (DNI).

### SUNAT Consulta RUC (scraping con Playwright)
- **URL:** `https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp`
- **Herramientas:** `playwright.async_api` + `BeautifulSoup`. Usa el navegador instalado (Chrome, luego Edge, luego Chromium de Playwright), viewport 1366x768, locale `es-PE`, `--disable-blink-features=AutomationControlled` y `navigator.webdriver` oculto (técnica del notebook, autorizada por el responsable del proyecto) para pasar la verificación de Cloudflare.
- **Flujo:** Digitar el RUC en `#txtRuc`, buscar con `#btnAceptar` y parsear la ficha desde los `.list-group-item .row`. Representantes legales y establecimientos anexos se obtienen interceptando `HTMLFormElement.prototype.submit` al pulsar cada botón y repitiendo el POST con `fetch` (respuesta decodificada en `iso-8859-1`), sin recargar la página.
- **Limitación:** Si SUNAT igual muestra la verificación de Cloudflare, la ficha se devuelve y la incidencia queda en `details` de la auditoría.
- **Alcance:** `SunatRucAdapter` (RUC de 11 dígitos) y `SunatDniAdapter` (DNI de 8 dígitos: busca por documento y abre la ficha del RUC de la persona natural). Un parámetro con formato inválido retorna `NO_DATA` sin abrir el navegador.
- **Timeouts:** 30 s para navegación y por selector. El navegador se cierra siempre en un bloque `finally`.
- **Windows:** Playwright exige `ProactorEventLoop`; si el bucle activo no lo es (p. ej. `uvicorn --reload`), el scraping corre en un hilo con su propio bucle.
- **Contrato del extractor:** `{"audit", "data", "raw"}` con `data` como `SunatProfile` (incluye `legal_representatives` y `branch_offices`).

### RNP Constancia (scraping con Playwright, solo RUC)
- **URL:** `https://www.rnp.gob.pe/Constancia/RNP_Constancia/ConsultaRuc.asp` (ASP clásico, sin API; el formulario exige un CAPTCHA de 6 caracteres).
- **Alcance:** Solo RUC (`RnpRucAdapter`). No admite DNI.
- **CAPTCHA:** El adaptador recibe un `CaptchaSolver` inyectable. Sin solver configurado devuelve `ERROR` ("CAPTCHA solver not configured") sin abrir el navegador.
- **Contrato del extractor:** `{"audit", "data", "raw"}` con `data` como `RnpRecord`.

---

## 5. Reglas de Código para Claude

- **Documentación OpenAPI en español latino:** Descripciones, resúmenes y ejemplos de Swagger en español; los nombres de campos, rutas y esquemas en inglés. Todo vive en `infrastructure/inbound/docs/` y en los `Field(description=...)` de `dto/response/`.

- **Nomenclatura en inglés:** Archivos, carpetas, clases, funciones, variables y modelos en inglés técnico. Cero mezcla de idiomas (los nombres de columnas de las fuentes externas se conservan solo al mapearlas).

- **Tipado estricto:** Usar type hints completos (`typing`, `pydantic`).
- **Código conciso:** No incluir comentarios obvios, explicaciones innecesarias ni código de relleno.
- **Manejo de errores:** Las fallas de una fuente no deben romper la ejecución de las demás; registrar incidencias en el bloque de auditoría.
- **SOLID y asincronía:** Métodos asíncronos (`async`/`await`) en operaciones de I/O de red.
- **Sin base de datos por ahora:** No agregar SQLAlchemy, SQLite ni migraciones de Alembic hasta que se indique explícitamente.