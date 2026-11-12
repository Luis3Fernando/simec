# SIMEC Backend

Backend asíncrono desarrollado en **FastAPI** bajo **arquitectura hexagonal (puertos y adaptadores)** para el monitoreo de mercados, consulta de proveedores del Estado y detección de conductas anticompetitivas.

El servicio actúa como un agregador y normalizador en tiempo real que extrae información pública mediante consultas HTTP directas (`httpx`) y automatización de navegadores (`Playwright`), consolidando perfiles empresariales (por **RUC** de 11 dígitos) y de personas naturales (por **DNI** de 8 dígitos) con trazabilidad de auditoría por cada fuente:

- **SUNAT (Consulta RUC):** Ficha tributaria, estado, condición, representantes legales y establecimientos anexos.
- **OECE / SEACE (Pentaho BI CDA):** Presencia en el RNP, vigencias, composición societaria (accionistas, representantes y órganos de administración) e historial de adjudicaciones y órdenes desde 2008.
- **OSCE — RNP (Constancia):** Historial de inscripciones por capítulo (bienes y servicios), códigos de proveedor y números de trámite con resolución automatizada de CAPTCHA.
- **APIS.NET.PE:** Pasarela rápida de validación de identidad (DNI) y padrón reducido (RUC).

---

## Requisitos previos

- **Python 3.11+**
- **pip** (gestor de paquetes de Python)
- **Google Chrome** o **Microsoft Edge** instalado en el sistema (utilizado por Playwright para las fuentes protegidas con anti-bot).

---

## Instalación y configuración

1. **Crear y activar el entorno virtual:**

   En Windows (PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   En Linux / macOS:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Actualizar pip e instalar las dependencias del proyecto:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Instalar los binarios de navegador para Playwright:**

   ```bash
   playwright install chromium
   ```

4. **Configurar las variables de entorno:**

   Copia el archivo de ejemplo `.env.example` a `.env` y ajusta los valores si es necesario.

   En Windows (PowerShell):
   ```powershell
   Copy-Item .env.example .env
   ```

   En Linux / macOS:
   ```bash
   cp .env.example .env
   ```

---

## Ejecución del proyecto

### 1. Levantar el servidor de desarrollo (FastAPI)

Desde la raíz del proyecto, ejecuta con `uvicorn`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Una vez iniciado el servidor, la documentación interactiva estará disponible en:

- **Swagger UI:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>

### 2. Endpoints principales

| Consulta | Endpoint | Fuentes |
|---|---|---|
| Consolidada por **RUC** (11 dígitos) | `GET http://localhost:8000/api/v1/companies/{ruc}` | apis.net.pe, SEACE, SUNAT y RNP |
| Consolidada por **DNI** (8 dígitos) | `GET http://localhost:8000/api/v1/persons/{dni}` | apis.net.pe, SEACE y SUNAT |

El RNP solo admite consultas por RUC. Cada respuesta incluye `audit_entries` con la duración, el estado (`SUCCESS`, `NO_DATA` o `ERROR`) y el detalle de cada fuente, de modo que una fuente caída no bloquea a las demás.

### 3. Ejecutar la suite de pruebas (pytest)

```bash
pytest -v
```

### 4. Laboratorio de exploración (Jupyter Notebooks)

Los cuadernos de pruebas y validación de fuentes se encuentran en la carpeta [`notebooks/`](notebooks/). Puedes abrirlos directamente desde VS Code seleccionando el kernel del entorno `.venv` o iniciando Jupyter Lab:

```bash
jupyter lab
```

---

## Mantenimiento de dependencias (pip)

Si instalas nuevas librerías durante el desarrollo con `pip install <paquete>`, actualiza el archivo `requirements.txt` ejecutando:

```bash
pip freeze > requirements.txt
```
