# Guía de Inicialización del Repositorio

Este documento describe cómo configurar y levantar cada componente del proyecto desde cero, en orden.

## Estado actual del proyecto

- **Backend** (FastAPI + LanceDB + OpenRouter): implementado (Specs 1–5).
- **Base de datos vectorial** (LanceDB): implementada y embebida en el backend.
- **Visor nativo** (C++/Qt 6 basado en Okular): implementado (`visor/`) (Specs 6).
- **Frontend** (React + TypeScript + Vite): implementado (`frontend/`), embebido en el visor vía QWebEngineView + Qt WebChannel (Specs 7–10).
- **Orquestación**: no existe `docker-compose`, `Makefile` ni scripts de orquestación. Cada componente se levanta por separado.

**Prerrequisito back-end:** **uv** (gestor de dependencias Python). Verificar con `uv --version`. Instalar si falta:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Orden de arranque

El visor nativo carga la UI de React desde `http://localhost:5173` (rutas `/chat` y `/library`) y el frontend llama al backend en `http://localhost:8000`. Por tanto, el orden es:

1. **Backend** (puerto 8000) → 2. **Frontend** (puerto 5173) → 3. **Visor** (Consume ambos).

---

## 1. Backend (FastAPI)

```bash
cd backend
uv sync                 # crea/actualiza .venv a partir de uv.lock (versionado)
cp .env.example .env    # asegura la configuración
```

Ejecutar el servidor (escucha en `127.0.0.1:8000`):

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

> ⚠️ **Seguridad:** una aparente clave real de OpenRouter está commiteada en `backend/.env.example`. Si es una clave válida, se debe rotar/revocar.

## 2. Base de datos vectorial (LanceDB)

**No requiere paso de inicialización.** LanceDB es una BD vectorial **embebida** (sin servidor). Las tablas `documents`, `chunks` y `chat_messages` se crean automáticamente al arrancar el backend:

- Gancho `lifespan` → `VectorDB.init_db()` en `backend/app/main.py`.
- Implementación: `backend/app/services/vector_db.py`.
- Datos en `backend/data/vector_db/` (gitignored).
- Ruta configurable con `VECTOR_DB_PATH="data/vector_db"`.

## 3. Frontend (React + TypeScript + Vite)

```bash
cd frontend
npm install      # instala dependencias desde package-lock.json
npm run dev      # servidor de desarrollo en http://localhost:5173
```

Nota: **el visor nativo espera el frontend en el puerto 5173** (por defecto). El frontend selecciona la vista según la ruta URL: `/chat` o `/library`. Si quieres que el visor apunte a otra URL, define la variable de entorno `DEV_URL` al lanzar el visor.

Scripts disponibles (`frontend/package.json`):
- `npm run dev` — servidor Vite de desarrollo.
- `npm run build` — `tsc -b && vite build`.
- `npm run lint` — `oxlint`.
- `npm run preview` — previsualizar build.

## 4. Aplicación de escritorio / Visor (C++ / Qt 6, basado en Okular)

El ejecutable resultante se llama `lector-visor` y se genera desde `visor/`.

### Prerrequisitos (Fedora)

```bash
sudo dnf install -y \
    gcc-c++ \
    cmake \
    extra-cmake-modules \
    qt6-qtbase-devel \
    kf6-kparts-devel \
    kf6-kxmlgui-devel \
    kf6-ki18n-devel \
    okular-devel \
    okular-libs \
    okular-part
```

### Compilación

```bash
cd visor
mkdir build && cd build
cmake ..    # configura con CMake
make        # genera el binario lector-visor
```

> El `CMakeLists.txt` además requiere los módulos Qt6 `WebEngineWidgets` y `WebChannel` (`find_package`). Si falla el paso de CMake, instala el paquete de desarrollo de Qt WebEngine (`qt6-qtwebengine-devel`) que no figura en la lista del README del visor.

### Ejecución

```bash
./lector-visor /ruta/al/documento.pdf
```

El visor:
- Carga el KPart de Okular para visualizar el PDF en la pestaña **Documento**.
- Embebe la UI de React (`http://localhost:5173/chat`) a la derecha, con comunicación bidireccional vía **Qt WebChannel** (`qtBridge`).
- Carga la pestaña **Biblioteca** con `/library` a pantalla completa.
- Registra atajos: `Alt+E` (explicar), `Alt+R` (resumir), `Alt+T` (copiar al chat).

Si se quiere apuntar a otra URL del frontend en vez de la de desarrollo:

```bash
DEV_URL=http://localhost:5173 ./lector-visor /ruta/al/documento.pdf
```

## Aplicación end-to-end (flujo integrado)

1. **Backend** arrancado en `:8000` (crea LanceDB automáticamente).
2. **Frontend** dev server en `:5173`.
3. **Visor** en ejecución; carga PDF y las pestañas React que consumen la API del backend (`http://localhost:8000/api/v1/...`).

Flujo de datos: **visor Okular ↔ Qt WebChannel ↔ React ↔ FastAPI (`:8000`) ↔ LanceDB ↔ OpenRouter**.

## Verificación

```bash
# Backend (tests con provider mock + BD vectorial temporal)
cd backend
uv run pytest
uv run ruff check .
uv run ruff format .
curl http://127.0.0.1:8000/api/v1/health

# Frontend
cd frontend
npm run lint
```

## Referencias clave

| Recurso | Ruta |
|---|---|
| Entrada backend | `backend/app/main.py` |
| Configuración | `backend/app/core/config.py` |
| BD vectorial | `backend/app/services/vector_db.py` |
| Dependencias backend | `backend/pyproject.toml`, `backend/uv.lock` |
| Template de entorno | `backend/.env.example` |
| Frontend | `frontend/` (`package.json`, `vite.config.ts`) |
| Visor C++/Qt | `visor/` (`CMakeLists.txt`, `README.md`) |
| Estado del proyecto | `ETAPAS DE DESARROLLO.md` |
| Arquitectura | `docs/propuesta_tecnica.md` |
| Planes por spec | `specs/<feature>/plan_implementacion.md` |