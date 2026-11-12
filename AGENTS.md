# SIMEC Backend — Contexto y arquitectura del sistema

## 1. Propósito del sistema
Backend de alta disponibilidad en **FastAPI** para el monitoreo de mercados y la detección de conductas anticompetitivas. Actúa como un agregador y normalizador asíncrono que consulta fuentes públicas y abiertas en tiempo real (por **RUC** de 11 dígitos o **DNI** de 8 dígitos), consolida perfiles tributarios, societarios, registrales, de contrataciones estatales y de presencia digital, y retorna estructuras tipadas con trazabilidad de auditoría íntegra por cada fuente.

En su fase actual, el sistema opera como pasarela de agregación en memoria, preparado estructuralmente para incorporar persistencia relacional o documental en la capa de infraestructura sin alterar el dominio ni los casos de uso.

---

## 2. Patrón arquitectónico: arquitectura hexagonal (puertos y adaptadores)

El proyecto aplica una separación estricta en tres capas concéntricas con inversión de dependencias hacia el interior:

1. **Dominio (`app/domain/`):**
   - Representa el núcleo puro del negocio sin dependencias hacia frameworks web (`FastAPI`), clientes de red (`httpx`, `playwright`) ni librerías de base de datos u ORMs.
   - **Modelos y entidades (`models/`):** Cada módulo modela la estructura de datos extraída de una fuente específica (`audit.py`, `profile.py`, `rnp.py`, `seace.py`, `sunat.py`). Está diseñado para escalar horizontalmente incorporando nuevos modelos conforme se integren más fuentes (registros públicos, prensa, Instagram, LinkedIn, Facebook, etc.).
   - **Objetos de valor (`value_objects/` — evolutivo):** A medida que crezcan las reglas de validación del negocio, el dominio puede incorporar *value objects* inmutables (por ejemplo, identificadores tributarios validados, rangos monetarios o razones sociales normalizadas).

2. **Aplicación (`app/application/`):**
   - Actúa como capa de conexión y orquestación entre el mundo exterior y el dominio.
   - **Objetos de transferencia de datos (`dto/`):** Conectan la entrada y salida de los casos de uso mediante estructuras inmutables en `command/` (`GetCompanyCommand`, `GetPersonCommand`) y `result/` (`CompanyResult`, `PersonResult`).
   - **Puertos de entrada (`port/usecase/`):** Interfaces abstractas que definen los casos de uso del sistema (`GetCompanyUseCase`, `GetPersonUseCase`) bajo el contrato `execute(command) -> result`.
   - **Puertos de salida (`port/out/`):** Interfaces abstractas que definen los contratos requeridos hacia el exterior, tanto para extracción de datos (`ExtractorPort`) como para futuros contratos de persistencia.
   - **Servicios de aplicación (`services/`):** Implementaciones concretas de los casos de uso (`get_company_service.py`, `get_person_service.py`) apoyadas en el orquestador concurrente (`source_runner.py`), que ejecuta múltiples puertos de salida en paralelo aislando fallos individuales.

3. **Infraestructura (`app/infrastructure/`):**
   - Contiene todos los adaptadores técnicos divididos según la dirección del flujo:
   - **Infraestructura de entrada (`infrastructure/inbound/`):** Capa de entrega HTTP REST en FastAPI. Agrupa controladores versionados (`controller/v1/`), esquemas de validación de entrada (`dto/request/`), modelos de respuesta (`dto/response/`), transformadores (`mapper/`) y documentación OpenAPI (`docs/`).
   - **Infraestructura de salida — Extractores (`infrastructure/outbound/extractors/`):** Implementaciones concretas de `ExtractorPort` organizadas por fuente (`profile`, `rnp`, `seace`, `sunat`, y futuras integraciones de redes o registros), conteniendo clientes HTTP/Playwright (`client.py`), adaptadores por documento (`ruc_adapter.py`, `dni_adapter.py`) y utilidades comunes (`shared/`).
   - **Infraestructura de salida — Persistencia (`infrastructure/outbound/persistence/` — proyectada):** Módulos de acceso a base de datos desacoplados del dominio, estructurados internamente en `entity/` (modelos del ORM), `repository/` (operaciones de consulta y guardado), `mapper/` (conversión entre entidad de base de datos y modelo de dominio) y `adapters/` (implementación de los puertos de salida de persistencia).

4. **Configuración e inyección de dependencias (`app/core/`):**
   - Ensambla las instancias concretas de `infrastructure/outbound/` dentro de los servicios de `application/services/` y las expone como dependencias inyectables para los controladores (`dependencies.py`).

---

## 3. Flujo de ejecución de una petición

```text
[Cliente HTTP]
      │
      ▼
1. Controlador de entrada (infrastructure/inbound/controller/v1/)
   ├── Valida el parámetro de ruta (RucPathParam / DniPathParam en dto/request/)
   └── Transforma la petición en Command mediante el mapper (inbound/mapper/)
      │
      ▼
2. Caso de uso y servicio orquestador (application/port/usecase/ -> application/services/)
   ├── Recibe el Command a través de la interfaz del caso de uso
   └── Coordina la ejecución asíncrona concurrente (source_runner.py)
      │
      ▼
3. Puertos y adaptadores de salida (application/port/out/ -> infrastructure/outbound/)
   ├── Extractores (outbound/extractors/): consultan fuentes externas y retornan {"audit", "data", "raw"}
   ├── Persistencia (outbound/persistence/ - proyectada): lectura/escritura vía adapters, repository, entity y mapper
   └── Las fallas individuales se encapsulan en AuditResult sin interrumpir el resto de fuentes
      │
      ▼
4. Consolidación y respuesta
   ├── El servicio ensambla el objeto de salida (CompanyResult / PersonResult en application/dto/result/)
   └── El mapper de entrada convierte el Result en CompanyResponse / PersonResponse (JSON)
```

## 4. Estructura del repositorio
```text
simec-backend/
├── app/
│   ├── domain/                                   # Núcleo del negocio (sin dependencias externas)
│   │   ├── models/                               # Entidades por fuente (audit, profile, rnp, seace, sunat, etc.)
│   │   └── value_objects/                        # Objetos de valor inmutables (según evolución del dominio)
│   │
│   ├── application/                              # Orquestación y casos de uso
│   │   ├── dto/
│   │   │   ├── command/                          # Objetos de entrada (GetCompanyCommand, GetPersonCommand)
│   │   │   └── result/                           # Objetos de salida (CompanyResult, PersonResult)
│   │   ├── port/
│   │   │   ├── usecase/                          # Interfaces de casos de uso (GetCompanyUseCase, GetPersonUseCase)
│   │   │   └── out/                              # Interfaces de salida (ExtractorPort, futuros puertos de repositorio)
│   │   └── services/                             # Implementación de casos de uso y source_runner.py
│   │
│   ├── infrastructure/                           # Adaptadores técnicos hacia el exterior
│   │   ├── inbound/                              # Adaptador primario HTTP (FastAPI)
│   │   │   ├── controller/v1/                    # company_controller.py, person_controller.py, router.py
│   │   │   ├── docs/                             # Especificaciones y ejemplos OpenAPI
│   │   │   ├── dto/
│   │   │   │   ├── request/                      # Validación de parámetros de entrada
│   │   │   │   └── response/                     # Esquemas Pydantic de respuesta HTTP
│   │   │   └── mapper/                           # Conversión Request <-> Command y Result <-> Response
│   │   │
│   │   └── outbound/                             # Adaptadores secundarios
│   │       ├── extractors/                       # Conectores por fuente (profile, rnp, seace, sunat, shared, etc.)
│   │       └── persistence/                      # Capa de base de datos (futura: adapters, entity, mapper, repository)
│   │
│   ├── core/                                     # Configuración global e inyección de dependencias
│   │   └── dependencies.py                       # Ensamblaje de adaptadores y servicios
│   └── main.py                                   # Punto de entrada de la aplicación FastAPI
│
├── notebooks/                                    # Laboratorio de exploración de fuentes (Jupyter)
├── tests/                                        # Pruebas automatizadas (pytest)
├── requirements.txt
└── AGENTS.md
```