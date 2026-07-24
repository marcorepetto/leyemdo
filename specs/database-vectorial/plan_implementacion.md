# Plan de Implementación: Spec 3 - Base de Datos Vectorial Local

Este plan detalla la estrategia paso a paso para la instalación de dependencias, desarrollo de la persistencia local con LanceDB, generación de embeddings mock deterministas, creación y actualización de endpoints y validación mediante pruebas unitarias e integración para la Spec 3.

---

## 1. Estrategia de Ejecución (Paso a Paso)

Debido al carácter secuencial y la cohesión de los componentes del backend, el desarrollo se realizará linealmente por el agente principal.

### Paso 1: Instalación de Dependencias
1. Ejecutar `uv add lancedb pyarrow` en el directorio `backend/`.
2. Ejecutar `uv sync` para sincronizar y actualizar el entorno virtual.

### Paso 2: Generador de Embeddings Mock Determinista (`backend/app/services/embeddings.py`)
1. Crear `backend/app/services/embeddings.py`.
2. Definir una interfaz o clase base `BaseEmbeddingService`.
3. Implementar la clase `MockEmbeddingService` que genere vectores de 768 dimensiones.
4. Usar el hash SHA-256 del texto de entrada como semilla (`random.seed`) para la generación del vector de manera que sea determinista y reproducible.

### Paso 3: Módulo de Base de Datos Vectorial (`backend/app/services/vector_db.py`)
1. Crear `backend/app/services/vector_db.py`.
2. Definir los esquemas Pydantic `DocumentModel` y `ChunkModel` heredando de `lancedb.pydantic.LanceModel`.
3. Implementar el cliente/manejador `VectorDB`:
   * Conexión a LanceDB persistida en `settings.VECTOR_DB_PATH`.
   * Método `init_db()` para inicializar y crear las tablas `documents` y `chunks` si no existen.
   * Método `add_document(doc_metadata, chunks_list)` para persistir datos.
   * Método `get_documents()` para retornar la lista de documentos.
   * Método `delete_document(document_id)` para borrar el documento de la tabla `documents` y todos sus chunks de la tabla `chunks`.
   * Método `search_chunks(query_vector, limit)` para realizar búsqueda vectorial aproximada sobre `chunks`.

### Paso 4: Inicialización de la DB en FastAPI (`backend/app/main.py`)
1. Modificar `backend/app/main.py` para llamar a la inicialización de la base de datos `VectorDB.init_db()` dentro del bloque de `lifespan`.

### Paso 5: Modificación de la Ingesta (`backend/app/services/ingest.py`)
1. Modificar `backend/app/services/ingest.py`.
2. Eliminar el uso de `IN_MEMORY_DB` para el almacenamiento final del documento e integrar `MockEmbeddingService` para generar los vectores para cada fragmento.
3. Llamar a `VectorDB.add_document` para persistir los chunks y metadatos una vez concluido el procesamiento.

### Paso 6: Actualización y Creación de Endpoints y Rutas
1. Modificar `backend/app/api/v1/endpoints/documents.py`:
   * Adaptar `/upload`, `/status` y `/chunks/{document_id}` para integrarse con LanceDB.
   * Modificar `GET /` (o la ruta correspondiente para listar documentos) para llamar a `VectorDB.get_documents()` y retornar el conteo de chunks.
   * Implementar `DELETE /{document_id}` para invocar a `VectorDB.delete_document()`.
2. Crear `backend/app/api/v1/endpoints/search.py`:
   * Implementar `GET /` para el endpoint `/api/v1/library/search`.
   * Aceptar parámetros `q` (consulta) y `limit` (por defecto 5).
   * Generar vector mock determinista para `q` y buscar en la base de datos vectorial de LanceDB.
3. Modificar `backend/app/api/v1/router.py` para registrar el nuevo endpoint de búsqueda (`search_router`).

### Paso 7: Suite de Pruebas Unitarias e Integradas
1. Crear `backend/tests/test_vector_db.py` para verificar de forma aislada las operaciones de inicialización, inserción, eliminación manual en cascada y búsqueda vectorial.
2. Adaptar `backend/tests/test_documents.py` para que utilice el nuevo almacenamiento y pruebe el flujo completo de ingesta y búsqueda semántica de punta a punta.

### Paso 8: Validación de Calidad
1. Ejecutar `uv run ruff check --fix .` y `uv run ruff format .` para verificar estilo y formato.
2. Validar que todas las pruebas pasen exitosamente con `uv run pytest`.

---

## 2. Plan de Asignación y Paralelización
La complejidad técnica es baja y secuencial, por lo que todo el código será implementado en un único hilo de ejecución por el agente principal.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Tras recibir la aprobación del usuario para este Plan de Implementación:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Comenzaremos la codificación paso a paso.
