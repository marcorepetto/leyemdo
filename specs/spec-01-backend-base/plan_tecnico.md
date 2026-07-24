# Plan Técnico: Spec 1 - Backend Base

Este plan técnico detalla la arquitectura de software, los archivos a crear o modificar, y las decisiones de diseño para la implementación de la infraestructura base del backend local en FastAPI.

---

## 1. Archivos Impactados

Dado que es la fase inicial, no hay archivos existentes modificados. Crearemos toda la estructura de soporte dentro de un directorio dedicado `backend/` en la raíz del repositorio.

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   └── health.py       <-- Endpoint de estado (/health)
│   │       ├── __init__.py
│   │       └── router.py           <-- Enrutador principal de la v1
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py               <-- Configuración con Pydantic-Settings
│   ├── __init__.py
│   └── main.py                     <-- Punto de entrada de FastAPI
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 <-- Configuración de pytest
│   └── test_health.py              <-- Prueba de integración del health check
├── .env.example                    <-- Plantilla de variables de entorno
├── pyproject.toml                  <-- Configuración de dependencias (uv)
└── ruff.toml                       <-- Configuración de Ruff (linter/formatter)
```

---

## 2. Detalle de los Archivos a Crear

### A. Dependencias y Configuración del Entorno (`backend/pyproject.toml`)
Definiremos las dependencias estrictas utilizando el estándar `pyproject.toml` gestionado por `uv`.
* **Herramienta:** `uv`
* **Dependencias de Producción:**
  * `fastapi`
  * `uvicorn[standard]`
  * `pydantic-settings`
* **Dependencias de Desarrollo:**
  * `pytest`
  * `httpx` (para pruebas asíncronas / cliente de pruebas de FastAPI)
  * `ruff`

### B. Variables de Entorno (`backend/.env.example`)
Estableceremos las variables de configuración clave del proyecto:
```ini
PROJECT_NAME="Lector PDF Inteligente API"
VERSION="0.1.0"
API_V1_STR="/api/v1"
HOST="127.0.0.1"
PORT=8000
LOG_LEVEL="INFO"
GEMINI_API_KEY="tu_gemini_api_key_aqui"
VECTOR_DB_PATH="data/vector_db"
```

### C. Sistema de Configuración (`backend/app/core/config.py`)
Utilizaremos `pydantic_settings.BaseSettings` para cargar, validar y tipar las variables anteriores. Esto asegura que la aplicación falle al arrancar si falta alguna variable de entorno obligatoria o si tiene el tipo incorrecto.

### D. Punto de Entrada (`backend/app/main.py`)
* Inicialización de FastAPI.
* Configuración de CORS middleware: se permitirá `allow_origins=["*"]` ya que el backend corre de forma local (localhost/127.0.0.1) como sidecar del cliente nativo.
* Inclusión del enrutador de la API versión 1.

### E. Endpoints de Salud (`backend/app/api/v1/endpoints/health.py`)
Un router básico con un único endpoint:
* `GET /health` -> retorna `{ "status": "ok", "version": "0.1.0" }`.

### F. Suite de Pruebas (`backend/tests/`)
* **`conftest.py`**: Proveerá un fixture `client` de pytest que inicialice un `TestClient` de FastAPI.
* **`test_health.py`**: Realizará una petición `GET` al endpoint `/health` y asertará que la respuesta sea HTTP `200` y devuelva el JSON esperado.

---

## 3. Integración con el Sistema
Este backend es completamente autocontenido y se ejecuta en su propio proceso de puerto local (por defecto `8000`). En las siguientes specs (especialmente Spec 6 y 7), la aplicación React se comunicará con este puerto para todas las consultas RAG.

---

## 4. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación del usuario para este Plan Técnico:
1. Realizaremos un **commit en git** con la planificación aprobada.
2. Escribiremos el **Plan de Implementación** detallando los comandos exactos a ejecutar con `uv` y el orden de creación de los archivos.
