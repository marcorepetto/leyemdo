# Plan Técnico: Spec 3 - Base de Datos Vectorial Local

Este plan técnico detalla los cambios, nuevas dependencias, diseño de base de datos e integración de servicios a implementar para la persistencia local con LanceDB y la búsqueda semántica.

---

## 1. Dependencias Nuevas
Añadiremos los paquetes necesarios para la base de datos vectorial y almacenamiento columnar en `backend/pyproject.toml`:
* **`lancedb`**: Base de datos vectorial embebida y serverless, que almacena los datos en formato Parquet localmente.
* **`pyarrow`**: Requisito de LanceDB para la manipulación y definición de esquemas de datos eficientes en memoria.

---

## 2. Archivos Impactados y Creados

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── documents.py    <-- MODIFICADO: Actualizar endpoints para consultar LanceDB
│   │       │   └── search.py       <-- NUEVO: Endpoint GET /library/search de búsqueda semántica
│   │       └── router.py           <-- MODIFICADO: Registrar el router de búsqueda
│   ├── core/
│   │   └── config.py               <-- MODIFICADO: Configurar constantes de embeddings/DB si es necesario
│   ├── services/
│   │   ├── embeddings.py           <-- NUEVO: Interfaz y Mock determinista de embeddings de 768d
│   │   ├── vector_db.py            <-- NUEVO: Cliente y operaciones CRUD/Búsqueda de LanceDB
│   │   └── ingest.py               <-- MODIFICADO: Integrar generación de embeddings y persistencia en LanceDB
│   └── main.py                     <-- MODIFICADO: Inicialización de LanceDB en el evento de inicio (lifespan)
├── tests/
│   ├── test_vector_db.py           <-- NUEVO: Pruebas unitarias de LanceDB, CRUD y búsqueda
│   └── test_documents.py           <-- MODIFICADO: Adaptar tests para usar base de datos persistente (con mock)
└── pyproject.toml                  <-- MODIFICADO: Adición de dependencias 'lancedb' y 'pyarrow'
```

---

## 3. Detalle de Diseño e Implementación

### A. Generador de Embeddings Mock (`backend/app/services/embeddings.py`)
* **Clase `MockEmbeddingService`**:
  * Expone el método `get_embeddings(texts: list[str]) -> list[list[float]]` y `get_query_embedding(query: str) -> list[float]`.
  * Genera vectores de 768 dimensiones (compatibles con Gemini `text-embedding-004`).
  * **Determinismo:** Utiliza la función hash SHA-256 del texto de entrada para inicializar el generador de números pseudo-aleatorios (`random.seed`). Esto garantiza que el mismo fragmento de texto o consulta siempre produzca el mismo vector, permitiendo comparar similitudes de forma predecible en las pruebas.

### B. Módulo de Base de Datos Vectorial (`backend/app/services/vector_db.py`)
* **Esquemas Pydantic / LanceDB (`LanceModel`)**:
  * **`DocumentModel`**:
    * `document_id` (str, hash SHA-256) - Clave primaria.
    * `filename` (str) - Nombre del archivo.
    * `pages_count` (int) - Cantidad de páginas del PDF.
    * `total_chars` (int) - Caracteres totales.
    * `added_at` (datetime) - Fecha de adición.
    * `tags` (list[str]) - Etiquetas de organización.
    * `reading_progress` (float) - Avance de lectura (0.0 a 100.0).
  * **`ChunkModel`**:
    * `chunk_id` (str) - Clave primaria única.
    * `document_id` (str) - ID de relación lógica.
    * `text` (str) - Texto del fragmento.
    * `page_number` (int) - Página de inicio (1-indexed).
    * `pages` (list[int]) - Páginas que abarca.
    * `char_start` (int) - Offset del caracter de inicio.
    * `char_end` (int) - Offset del caracter de fin.
    * `section` (str, opcional) - Nombre de la sección.
    * `vector` (Vector(768)) - Representación vectorial.
* **Cliente de Base de Datos `VectorDB`**:
  * Utiliza un singleton o instancia compartida del cliente conectado a `settings.VECTOR_DB_PATH`.
  * **`init_db()`**: Asegura la creación de las tablas `documents` y `chunks` utilizando los esquemas anteriores.
  * **`add_document(doc: DocumentModel, chunks: list[ChunkModel])`**: Inserta registros en ambas tablas.
  * **`get_documents()`**: Consulta la tabla `documents`. Itera u obtiene conteos agregados para devolver el número de chunks de cada documento.
  * **`delete_document(document_id: str)`**: Realiza el borrado manual en cascada (elimina el registro del documento de la tabla `documents` y filtra y borra todos los chunks cuyo `document_id` coincida).
  * **`search_chunks(query_vector: list[float], limit: int)`**: Ejecuta una búsqueda vectorial aproximada sobre la tabla `chunks` y devuelve los fragmentos más similares con sus correspondientes metadatos.

### C. Modificación del Ingest Pipeline (`backend/app/services/ingest.py`)
* En lugar de escribir en `IN_MEMORY_DB`, el orquestador ahora:
  1. Instancia `MockEmbeddingService`.
  2. Genera los embeddings para cada fragmento segmentado.
  3. Crea una instancia de `DocumentModel` y una lista de `ChunkModel` con sus respectivos vectores.
  4. Llama a `VectorDB.add_document` para persistir los datos en LanceDB.
* Mantiene el diccionario `TASK_STATUS` en memoria únicamente para el estado de las tareas de procesamiento asíncronas en ejecución (es normal que los estados de tareas sean efímeros).

### D. Endpoints de la API
* **`GET /api/v1/library/documents`** (Modificado):
  * Invoca a `VectorDB.get_documents()`.
  * Devuelve la lista completa de documentos con sus metadatos y el conteo de chunks.
* **`DELETE /api/v1/library/documents/{document_id}`** (Nuevo):
  * Llama a `VectorDB.delete_document(document_id)`.
  * Lanza error HTTP 404 si el documento no existe.
* **`GET /api/v1/library/search`** (Nuevo):
  * Parámetros: `q: str` (consulta en lenguaje natural) y `limit: int = 5`.
  * Llama a `MockEmbeddingService` para obtener el vector de consulta de `q`.
  * Llama a `VectorDB.search_chunks` y devuelve el top K de chunks con mayor puntuación de similitud, incluyendo texto, metadatos y score.

---

## 4. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación del usuario para este Plan Técnico:
1. Realizaremos un **commit en git** con la planificación aprobada.
2. Escribiremos el **Plan de Implementación** detallando los pasos exactos a seguir.
