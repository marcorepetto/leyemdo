# Plan Técnico: Spec 4 - Integración de LLM (OpenRouter/Gemini) y Lógica ZDP

Este plan técnico detalla los cambios, nuevas dependencias, diseño de base de datos e integración de la API de OpenRouter y el tutor interactivo ZDP.

---

## 1. Dependencias Nuevas
Añadiremos los paquetes necesarios para la conexión y el streaming a `backend/pyproject.toml`:
* **`httpx`**: Cliente HTTP asíncrono para Python, necesario para realizar peticiones asíncronas a OpenRouter con streaming y SSE.
* **`sse-starlette`**: Utilidad para simplificar la entrega de Server-Sent Events (SSE) en FastAPI para el streaming de tokens de respuesta del LLM.

---

## 2. Archivos Impactados y Creados

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── chat.py         <-- NUEVO: Endpoints de chat (message/streaming, history, clear)
│   │       └── router.py           <-- MODIFICADO: Registrar el router de chat
│   ├── core/
│   │   └── config.py               <-- MODIFICADO: Variables de entorno de OpenRouter y dimensiones de embeddings
│   ├── services/
│   │   ├── embeddings.py           <-- MODIFICADO: Integrar OpenRouter para embeddings reales (2048d)
│   │   ├── openrouter.py           <-- NUEVO: Servicio cliente para llamadas HTTP a OpenRouter (embeddings y chat)
│   │   ├── prompt_templates.py     <-- NUEVO: Plantillas de prompts y andamiaje ZDP (tutor socrático/híbrido)
│   │   └── vector_db.py            <-- MODIFICADO: Agregar esquema y CRUD de la tabla 'chat_messages' y cambiar dimensión de chunks a 2048
│   └── main.py                     <-- MODIFICADO: No requiere cambios adicionales si VectorDB inicializa la nueva tabla
├── tests/
│   ├── test_openrouter.py          <-- NUEVO: Pruebas del servicio cliente de OpenRouter (con mocks de requests)
│   └── test_chat.py                <-- NUEVO: Pruebas de integración de endpoints del chat y RAG conversacional
└── pyproject.toml                  <-- MODIFICADO: Adición de dependencias 'httpx' y 'sse-starlette'
```

---

## 3. Detalle de Diseño e Implementación

### A. Configuración Híbrida (`backend/app/core/config.py`)
* Agregar las siguientes constantes de configuración:
  * `OPENROUTER_API_KEY`: str = ""
  * `EMBEDDING_PROVIDER`: str = "openrouter" # "openrouter", "gemini" o "mock"
  * `EMBEDDING_MODEL`: str = "nvidia/nemotron-3-embed-1b:free"
  * `EMBEDDING_DIMENSION`: int = 2048 # Nemotron = 2048, Gemini = 768
  * `LLM_PROVIDER`: str = "openrouter" # "openrouter" o "gemini"
  * `LLM_MODEL`: str = "nvidia/nemotron-3-ultra-550b-a55b:free"

### B. Servicio de Cliente OpenRouter (`backend/app/services/openrouter.py`)
* Implementar `OpenRouterService` utilizando `httpx.AsyncClient` para:
  * `async def get_embeddings(texts: list[str]) -> list[list[float]]`: Llama al endpoint de embeddings de OpenRouter.
  * `async def get_chat_stream(messages: list[dict]) -> AsyncGenerator[str, None]`: Llama al endpoint de chat completions con `stream=True` y yieldea los tokens de respuesta en tiempo real.

### C. Proveedor de Embeddings Flexible (`backend/app/services/embeddings.py`)
* Crear una fábrica o refactorizar el servicio de embeddings para instanciar dinámicamente el proveedor correcto según `settings.EMBEDDING_PROVIDER`:
  * Si es `"mock"`: Retorna `MockEmbeddingService(dimension=settings.EMBEDDING_DIMENSION)`.
  * Si es `"openrouter"`: Retorna `OpenRouterEmbeddingService()` que usa `OpenRouterService`.
  * Si es `"gemini"`: (Reservado para integración nativa de Gemini en Spec 4 posterior si se requiere).

### D. Modelos de LanceDB y Persistencia del Chat (`backend/app/services/vector_db.py`)
* **Cambio de Dimensión:** Modificar la tabla `chunks` para utilizar `Vector(2048)` en lugar de `Vector(768)`.
* **Esquema de Chat:**
  * **`ChatMessageModel`**:
    * `message_id` (str) - Clave primaria (UUID).
    * `document_id` (str) - ID de relación con el documento.
    * `role` (str) - Rol de emisor (`user` o `assistant`).
    * `content` (str) - Contenido de texto del mensaje.
    * `timestamp` (datetime) - Fecha de creación.
    * `reasoning_details` (str | None) - Cadena de razonamiento opcional.
* **Operaciones de Mensajes:**
  * `add_chat_messages(messages: list[ChatMessageModel])`: Inserta registros en la tabla `chat_messages`.
  * `get_chat_history(document_id: str) -> list[dict]`: Recupera el historial completo ordenado por fecha.
  * `clear_chat_history(document_id: str)`: Borra todos los mensajes asociados a ese PDF.
* **Resiliencia en `init_db()`**: Asegura la inicialización de la tabla `chat_messages` con `exist_ok=True`.

### E. Plantillas de Prompts ZDP (`backend/app/services/prompt_templates.py`)
* Definir la plantilla del **System Prompt** para guiar al modelo a actuar bajo la lógica ZDP (Tutor Híbrido):
  * **Instrucciones:** Explicar didácticamente los conceptos clave con base en el contexto, estructurar la explicación de forma concisa y finalizar con una pregunta guía o un ejercicio rápido que invite a la reflexión activa y autoevaluación.
  * **Inyección de contexto:** Integrar los Top K chunks recuperados en una sección `[CONTEXTO]` claramente delimitada.

### F. API Endpoints del Chat (`backend/app/api/v1/endpoints/chat.py`)
* **`POST /message`**:
  * Toma `document_id` y `message`.
  * Llama al servicio de embeddings para vectorizar la consulta del usuario.
  * Llama a `VectorDB.search_chunks` para obtener los 5 fragmentos más relevantes del documento.
  * Obtiene el historial del chat mediante `VectorDB.get_chat_history`.
  * Construye la lista de mensajes (System prompt ZDP + Historial + Nueva consulta).
  * Llama a `OpenRouterService.get_chat_stream`.
  * Devuelve una respuesta de tipo `EventSourceResponse` (SSE) que transmite los tokens generados por el LLM en tiempo real.
  * **Guardado en segundo plano:** Tras finalizar el stream, el backend persiste el mensaje del usuario y la respuesta generada en la tabla `chat_messages`.
* **`GET /history/{document_id}`**:
  * Llama a `VectorDB.get_chat_history` y devuelve el JSON.
* **`DELETE /history/{document_id}`**:
  * Llama a `VectorDB.clear_chat_history` y devuelve confirmación.

---

## 4. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación del usuario para este Plan Técnico:
1. Realizaremos un **commit en git** con la planificación aprobada.
2. Escribiremos el **Plan de Implementación** detallando los pasos exactos a seguir.
