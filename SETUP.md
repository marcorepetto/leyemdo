# Guía de Inicialización del Repositorio

Este documento describe cómo configurar y levantar cada componente del proyecto desde cero.

## Estado actual del proyecto

- **Backend** (FastAPI + LanceDB + OpenRouter): implementado (Specs 1–4 + tool de debug).
- **Base de datos vectorial** (LanceDB): implementada y embebida en el backend.
- **Frontend** (fork de Okular C++/Qt + React vía QWebEngineView): **no implementado** (Specs 6–10 pendientes).
- **Orquestación**: no existe `docker-compose`, `Makefile` ni scripts; solo el gestor `uv`.

Requisito previo: **uv** (gestor de dependencias). Verificar con `uv --version`. Instalar si falta:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 1. Backend (FastAPI)

Desde la raíz del repositorio:

```bash
cd backend
uv sync                 # crea/actualiza .venv a partir de uv.lock (pinned)
cp .env.example .env    # asegura la configuración (un .env ya existe si no)
```

Ejecutar el servidor (ancla en `127.0.0.1:8000`):

```bash
uv run uvicorn app.main:app --reload
# o directamente: .venv/bin/uvicorn app.main:app --reload
```

- Documentación interactiva: http://127.0.0.1:8000/docs
- OpenAPI: `/api/v1/openapi.json`
- Health: `GET /api/v1/health`

Configuración en `backend/app/core/config.py` (cargada de `.env` vía pydantic-settings).

**Secretos requeridos:**
- `OPENROUTER_API_KEY` — obligatoria para embeddings, chat (SSE) y reranking reales.
- `GEMINI_API_KEY` — definida pero no en uso activo (alternativa documentada).

> ⚠️ **Seguridad:** una aparente clave real de OpenRouter está commiteada en `backend/.env.example` y `backend/.env`. Si es una clave válida, se debe rotar/revocar.

## 2. Base de datos vectorial (LanceDB)

**No requiere paso de inicialización.** LanceDB es una BD vectorial **embebida** (sin servidor). Las tablas `documents`, `chunks` y `chat_messages` se crean automáticamente al arrancar el backend:

- Gancho `lifespan` → `VectorDB.init_db()` en `backend/app/main.py`.
- Implementación: `backend/app/services/vector_db.py`.
- Datos en `backend/data/vector_db/` (gitignored).
- Ruta configurable con `VECTOR_DB_PATH="data/vector_db"`.

## 3. Frontend

**Aún no implementado.** No hay `frontend/`, `package.json` ni build. Arquitectura prevista (`docs/propuesta_tecnica.md`):

- **Okular (C++/Qt)** como visor PDF nativo.
- **React + TypeScript** (paneles chat/biblioteca) embebidos vía **QWebEngineView**.
- **Qt WebChannel** como IPC C++ ↔ React.

Único artefacto frontend actual: UI de debug en HTML servida por el backend en `GET /api/v1/debug/ui`.

## 4. Aplicación (integración)

Sin orquestador: la "aplicación" hoy es el propio backend. Flujo de ingestión vía `BackgroundTask` (`backend/app/services/ingest.py`): parseo PyMuPDF → chunking → embeddings (OpenRouter/mock) → persistencia en LanceDB.

Flujo previsto completo: **Okular ↔ WebChannel ↔ React ↔ FastAPI sidecar ↔ LanceDB ↔ OpenRouter**.

## Verificación

```bash
cd backend
uv run pytest                    # tests (provider mock + BD vectorial temporal)
uv run ruff check .              # lint
uv run ruff format .             # formato
curl http://127.0.0.1:8000/api/v1/health
```

## Referencias clave

| Recurso | Ruta |
|---|---|
| Entrada backend | `backend/app/main.py` |
| Configuración | `backend/app/core/config.py` |
| BD vectorial | `backend/app/services/vector_db.py` |
| Dependencias | `backend/pyproject.toml`, `backend/uv.lock` |
| Template de entorno | `backend/.env.example` |
| Estado del proyecto | `ETAPAS DE DESARROLLO.md` |
| Arquitectura | `docs/propuesta_tecnica.md` |
| Instrucciones de ejecución | `specs/backend-base/plan_implementacion.md` |