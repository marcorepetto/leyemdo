# Plan de Implementación: Spec 4 - Integración de LLM y Lógica ZDP

Este plan detalla la estrategia paso a paso para la instalación de dependencias, configuración de variables, desarrollo del cliente de OpenRouter, extensión de la base de datos vectorial local, inyección de prompts ZDP, creación de endpoints y validación de calidad para la Spec 4.

---

## 1. Estrategia de Ejecución (Paso a Paso)

Debido al flujo continuo de RAG y la integración de APIs externas, el desarrollo se realizará linealmente por el agente principal.

### Paso 1: Instalación de Dependencias
1. Ejecutar `uv add httpx sse-starlette` en el directorio de `backend/`.
2. Ejecutar `uv sync` para actualizar el entorno virtual.

### Paso 2: Configuración del Proyecto (`backend/app/core/config.py`)
1. Agregar las variables para OpenRouter y configuración híbrida (`OPENROUTER_API_KEY`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `LLM_PROVIDER`, `LLM_MODEL`) en `Settings`.
2. Agregar variables de ejemplo correspondientes en `backend/.env.example`.

### Paso 3: Cliente OpenRouter (`backend/app/services/openrouter.py`)
1. Crear `backend/app/services/openrouter.py`.
2. Implementar la clase asíncrona `OpenRouterService` utilizando `httpx.AsyncClient` para:
   * Generar embeddings reales de 2048d ( Nemotron-3 ) para listas de textos.
   * Consumir chat completions con streaming (`stream=True`) y procesar la respuesta SSE de OpenRouter para transmitirla token por token.

### Paso 4: Refactor del Módulo de Embeddings (`backend/app/services/embeddings.py`)
1. Implementar la clase `OpenRouterEmbeddingService` utilizando `OpenRouterService`.
2. Crear un factory function `get_embedding_service() -> BaseEmbeddingService` que devuelva la instancia adecuada según `settings.EMBEDDING_PROVIDER`.
3. Esto permitirá a los tests y a la ingesta local conmutar dinámicamente entre embeddings reales y mock.

### Paso 5: Persistencia del Chat y LanceDB (`backend/app/services/vector_db.py`)
1. Modificar `ChunkModel` para usar `Vector(2048)` como dimensión predeterminada.
2. Definir el esquema `ChatMessageModel` heredando de `lancedb.pydantic.LanceModel`.
3. Modificar `init_db()` para inicializar la nueva tabla `chat_messages`.
4. Implementar en `VectorDB` las operaciones para:
   * `add_chat_messages(messages: list[ChatMessageModel])`.
   * `get_chat_history(document_id: str) -> list[dict]` (ordenado por fecha).
   * `clear_chat_history(document_id: str)`.

### Paso 6: Plantillas de Prompts ZDP (`backend/app/services/prompt_templates.py`)
1. Crear `backend/app/services/prompt_templates.py`.
2. Escribir las directrices pedagógicas de tutoría (ZDP) y la plantilla para inyectar el contexto del documento de forma estructurada.

### Paso 7: Integración en la Ingesta (`backend/app/services/ingest.py`)
1. Modificar `run_ingest_pipeline` para resolver el servicio de embeddings usando `get_embedding_service()`.
2. Esto indexará automáticamente los fragmentos con vectores reales de 2048d (o mock según la configuración).

### Paso 8: Endpoints del Chat y Registro de Rutas
1. Crear `backend/app/api/v1/endpoints/chat.py`.
2. Implementar las rutas del chat:
   * `POST /message` (RAG + historial + streaming SSE).
   * `GET /history/{document_id}` (historial).
   * `DELETE /history/{document_id}` (limpiar).
3. Modificar `backend/app/api/v1/router.py` para registrar `chat.router` bajo el prefijo `"/chat"`.

### Paso 9: Pruebas Unitarias e Integración
1. Crear `backend/tests/test_openrouter.py` para probar de forma aislada el cliente de OpenRouter simulando respuestas API usando mocks de HTTPX.
2. Crear `backend/tests/test_chat.py` para validar los endpoints de chat, el historial conversacional y la integración con RAG.

### Paso 10: Validación de Calidad
1. Ejecutar `uv run ruff check --fix .` y `uv run ruff format .` para formatear el código.
2. Correr la suite completa de pytest.

---

## 2. Plan de Asignación y Paralelización
Al tratarse de una integración secuencial en el backend, todo el desarrollo será realizado por el agente principal.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Tras recibir la aprobación del usuario para este Plan de Implementación:
1. Realizaremos un **commit en git** con el plan aprobado.
2. Comenzaremos la codificación paso a paso.
