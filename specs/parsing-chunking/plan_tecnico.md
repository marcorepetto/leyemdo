# Plan Técnico: Spec 2 - Parsing & Chunking

Este plan técnico detalla los cambios, nuevas dependencias y estructura de servicios a implementar para el procesamiento de PDFs y la segmentación de texto.

---

## 1. Dependencias Nuevas
Añadiremos la librería de procesamiento PDF a `backend/pyproject.toml`:
* **`pymupdf` (fitz):** Para interactuar con los PDFs de forma rápida, obtener el texto y los metadatos de las páginas.

---

## 2. Archivos Impactados y Creados

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── documents.py    <-- NUEVO: Endpoints de subida, estado y chunks
│   │       │   └── health.py
│   │       └── router.py           <-- MODIFICADO: Registro del router de documentos
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py           <-- NUEVO: Extractor y limpiador de PDFs (PyMuPDF)
│   │   ├── text_splitter.py        <-- NUEVO: Recursive splitter con tracking de páginas
│   │   └── ingest.py               <-- NUEVO: Orquestador y BackgroundTask de ingesta
│   ├── main.py
│   └── ...
├── tests/
│   ├── conftest.py
│   └── test_documents.py          <-- NUEVO: Pruebas del pipeline de ingesta
└── pyproject.toml                  <-- MODIFICADO: Adición de 'pymupdf'
```

---

## 3. Detalle de Diseño e Implementación

### A. Parser de PDF (`backend/app/services/pdf_parser.py`)
* **Extracción:** Usa `fitz.open(stream=file_bytes)` para abrir el PDF en memoria.
* **Layout:** Itera por páginas extrayendo texto con `page.get_text("text", sort=True)` (asegura orden correcto de columnas).
* **Limpieza:**
  * Une guiones rotos de fin de línea (`word-\nwrap` -> `wordwrap`).
  * Normaliza espacios en blanco duplicados.
* **Retorno:** Una lista de diccionarios, uno por página, conteniendo el texto limpio, su longitud y la página física.

### B. Segmentador Inteligente (`backend/app/services/text_splitter.py`)
* **Algoritmo:** Implementación simplificada de `RecursiveCharacterTextSplitter`. Divide recursivamente por saltos de párrafo (`\n\n`), saltos de línea (`\n`), puntos y espacios.
* **Parámetros:** Configurable por `chunk_size` y `chunk_overlap`.
* **Mapeo de Páginas:**
  * En lugar de procesar páginas de forma aislada, el splitter procesa el flujo continuo del texto.
  * Mantiene una estructura de offsets para saber a qué página pertenece cada caracter. Al crear un chunk, determina la página inicial (`page_number`) y la lista de todas las páginas cruzadas (`pages`).
* **Secciones:** Busca coincidencias al inicio del chunk que asemejen títulos de sección (ej: `"1. Introduction"`, `"References"`, `"Abstract"`) mediante expresiones regulares para asignar el metadato `section`.

### C. Orquestador de Ingesta (`backend/app/services/ingest.py`)
* Contiene una variable global en memoria para persistencia temporal:
  * `IN_MEMORY_DB: dict[str, dict]` (clave: `document_id`).
  * `TASK_STATUS: dict[str, dict]` (clave: `task_id`).
* **Función `run_ingest_pipeline(task_id, document_id, file_bytes, profile)`:**
  * Cambia estado de la tarea a `processing`.
  * Llama a `pdf_parser` para extraer texto de todas las páginas.
  * Llama a `text_splitter` con los parámetros del perfil (`paper` -> 500, `book` -> 1000).
  * Guarda el resultado (metadatos del doc + lista de chunks) en `IN_MEMORY_DB`.
  * Cambia el estado de la tarea a `completed` con el `document_id` asociado.

### D. Endpoints de la API (`backend/app/api/v1/endpoints/documents.py`)
* `POST /upload`:
  * Calcula el hash SHA-256 del archivo para generar el `document_id`.
  * Si el documento ya existe en `IN_MEMORY_DB`, responde directamente con el `document_id` y estado `completed` para ahorrar procesamiento.
  * Si no existe, genera un `task_id` único (UUID), inicializa su estado como `processing`, y arranca `run_ingest_pipeline` en un `BackgroundTasks` de FastAPI.
  * Retorna HTTP 202 con el `task_id` y `document_id`.
* `GET /status/{task_id}`:
  * Retorna el estado actual de la tarea.
* `GET /chunks/{document_id}`:
  * Retorna la lista de chunks procesados para ese documento.

---

## 4. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación del usuario para este Plan Técnico:
1. Realizaremos un **commit en git** con la planificación aprobada.
2. Escribiremos el **Plan de Implementación** detallando los pasos exactos a seguir.
