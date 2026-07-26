# Plan Técnico: Spec 5 - Servicios de Acción Contextual

Este plan técnico detalla la arquitectura de software, los archivos a crear o modificar, y las decisiones de diseño para la implementación de los servicios de acciones contextuales (Explicar, Traducir, Buscar Relacionado, y Soporte Interno).

---

## 1. Archivos Impactados

Para esta especificación, agregaremos un nuevo router de endpoints y ampliaremos los servicios y las pruebas existentes:

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── context.py          <-- NUEVO: Endpoints de acción contextual
│   │       └── router.py               <-- MODIFICADO: Registro del router de contexto
│   └── services/
│       └── prompt_templates.py         <-- MODIFICADO: Prompts para explicación y traducción
└── tests/
    └── test_context.py                 <-- NUEVO: Pruebas de integración de contexto
```

---

## 2. Detalle de los Cambios y Nuevos Archivos

### A. Plantillas de Prompts (`backend/app/services/prompt_templates.py`)
Añadiremos plantillas dedicadas para las tareas de explicación y traducción rápida en el backend:

```python
SYSTEM_PROMPT_EXPLAIN = """Eres un asistente de lectura científica y académica. Tu tarea es explicar de forma clara, directa y concisa el fragmento de texto seleccionado por el usuario. 

Sigue estas directrices:
1. Responde de forma resumida e informativa, optimizada para una ventana emergente o tooltip rápida.
2. No uses andamiaje pedagógico (ZDP) ni plantees contra-preguntas al final, ya que el usuario está en medio de la lectura del documento.
3. Utiliza el contexto adjunto del documento si es útil para aclarar términos ambiguos o referencias internas.

[CONTEXTO]
{context}
"""

SYSTEM_PROMPT_TRANSLATE = """Eres un traductor experto en textos científicos y académicos. Tu única tarea es traducir el fragmento de texto seleccionado al idioma de destino solicitado: '{target_language}'.

Directrices:
1. Mantén la precisión técnica, la jerga científica y el significado conceptual original.
2. Retorna ÚNICAMENTE la traducción limpia del fragmento. No agregues introducciones ("Aquí está la traducción:"), notas al pie ni comentarios explicativos.
"""

def compile_explain_prompt(selected_text: str, context_chunks: list[dict]) -> str:
    # Compilación similar a compile_tutor_prompt usando los chunks recuperados
    ...
```

### B. Endpoints de Contexto (`backend/app/api/v1/endpoints/context.py`)
Implementaremos los endpoints bajo el esquema FastAPI:

1. **`POST /api/v1/context/explain`**
   * **Payload:** `ContextActionRequest` (contiene `selected_text`, `document_id`)
   * **Lógica:**
     1. Obtiene chunks contextuales internos para la selección (usando similitud vectorial en LanceDB filtrada por el `document_id` actual).
     2. Compila el prompt con `SYSTEM_PROMPT_EXPLAIN`.
     3. Llama a la API de OpenRouter/Gemini sin streaming (espera el resultado JSON completo) y retorna `{ "explanation": text_explicado }`.

2. **`POST /api/v1/context/translate`**
   * **Payload:** `ContextActionRequest` (contiene `selected_text`, `target_language`)
   * **Lógica:**
     1. Llama al LLM pasándole el texto seleccionado junto con el prompt `SYSTEM_PROMPT_TRANSLATE` formateado con `target_language`.
     2. Retorna `{ "translation": text_traducido }`.

3. **`POST /api/v1/context/search-related`**
   * **Payload:** `ContextActionRequest` (contiene `selected_text`, `document_id`, `limit`)
   * **Lógica:**
     1. Genera embedding de `selected_text`.
     2. Busca chunks en LanceDB con un límite mayor (p. ej., `vector_limit = 20`).
     3. Filtra la lista en memoria para conservar solo chunks donde `document_id != request.document_id`.
     4. Si el Reranking está activo, envía el texto seleccionado y los candidatos de otros documentos al reranker de OpenRouter, retornando el top `limit`.
     5. Si no está activo o falla, hace fallback al top `limit` vectorial original.
     6. Retorna la lista de fragmentos similares encontrados en otros documentos.

4. **`POST /api/v1/context/support`**
   * **Payload:** `ContextActionRequest` (contiene `selected_text`, `document_id`, `limit`)
   * **Lógica:**
     1. Genera embedding de `selected_text`.
     2. Busca en LanceDB chunks con filtro estricto `document_id == request.document_id`.
     3. Retorna la lista de chunks de soporte interno (incluyendo el número de página original y texto).

### C. Registro del Router (`backend/app/api/v1/router.py`)
Registrar el nuevo endpoint de FastAPI:
```python
from app.api.v1.endpoints import context
# ...
api_router.include_router(context.router, prefix="/context", tags=["context"])
```

### D. Pruebas Unitarias (`backend/tests/test_context.py`)
Desarrollar pruebas usando `pytest` que:
* Mockericen las llamadas a OpenRouter/Gemini para `explain`, `translate` y `rerank`.
* Validar que `/api/v1/context/search-related` retorne correctamente chunks excluyendo el documento de origen.
* Validar que `/api/v1/context/support` retorne únicamente chunks pertenecientes al documento de origen.

---

## 3. Próxima Fase (Fase 3: Plan de Implementación)
Una vez aprobado este Plan Técnico:
1. Se creará el plan de desarrollo e implementación secuencial.
2. Iniciaremos el proceso de codificación.
