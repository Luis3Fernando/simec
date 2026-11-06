# Bitácora de Exploración de Fuentes

## 1. OSCE – Ficha Única del Proveedor
* **Estado:** Validado técnicamente.
* **Dominio base:** `https://eap.oece.gob.pe`
* **Endpoint confirmado:** `/perfilprov-bus/1.0/tarjetas`
* **Método HTTP:** `GET`
* **Parámetros obligatorios:** `searchText`, `pageSize=6`, `pageNumber=1`, `export=1`, `langTag=es`
* **Cabeceras requeridas:**
  * `User-Agent`: Navegador estándar (Chrome/Edge).
  * `Referer`: `https://apps.oece.gob.pe/perfilprov-ui/`
* **Comportamiento ante respuestas:**
  * **Con datos:** Retorna HTTP `200 OK` con colección `tarjetasProvT01`.
  * **Sin resultados:** Retorna HTTP `200 OK` con `searchInfo.hitsTotal = 0` y arreglo vacío.
* **Destino en arquitectura:** Listo para encapsular en `app/adapters/outbound/extractors/osce/`.

## 2. SEACE – Antecedentes de Proveedores (Pentaho BI)
* **Estado:** En evaluación técnica.
* **Dominio base:** `https://bi.seace.gob.pe`
* **Ruta de acceso:** `/pentaho/api/repos/:public:ANTECEDENTES_PROVEEDORES:ANTECEDENTES_PROVEEDORES.wcdf/generatedContent`
* **Observación arquitectónica:** Es un dashboard analítico en Pentaho con autenticación pública (`userid=public&password=key`). Las consultas interactivas se ejecutan vía endpoints CDA asíncronos que devuelven estructuras tabulares o renderizan componentes HTML complejos.