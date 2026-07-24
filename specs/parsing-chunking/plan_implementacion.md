# Plan de Implementación: Spec 2 - Parsing & Chunking

Este plan detalla la estrategia paso a paso para la instalación de dependencias, desarrollo de servicios de procesamiento de PDF, endpoints y tests asociados para la Spec 2.

---

## 1. Estrategia de Ejecución (Paso a Paso)

Debido al carácter autocontenido y secuencial de la infraestructura de datos del backend, la implementación será lineal y ejecutada directamente por el agente principal.

### Paso 1: Instalación de Dependencias
1. Ejecutar `uv add pymupdf` en la carpeta `backend/` para integrar la librería de procesamiento de PDF.
2. Correr `uv sync` para actualizar el entorno virtual.

### Paso 2: Desarrollo del Parser de PDF (`backend/app/services/pdf_parser.py`)
1. Implementar la extracción de texto iterando páginas físicas usando `page.get_text("text", sort=True)`.
2. Implementar funciones de limpieza:
   * Normalización de espacios y saltos de línea.
   * Unión de guiones de final de línea (`\w+-\s*\n\s*\w+` -> palabra completa).
3. Estructurar el retorno indicando el texto y la longitud de cada página para facilitar el cálculo de offsets.

### Paso 3: Desarrollo del Segmentador de Texto (`backend/app/services/text_splitter.py`)
1. Implementar la división recursiva basada en caracteres (`\n\n`, `\n`, `.`, ` `).
2. Desarrollar la lógica de mapeo de offsets:
   * Concatenar el texto de las páginas manteniendo un registro de índices acumulativos (offsets).
   * Al segmentar, mapear los índices `char_start` y `char_end` del chunk contra los offsets de las páginas para determinar qué páginas (`pages: List[int]`) abarca.
3. Añadir detección simple de títulos de sección usando regex al inicio de los chunks.

### Paso 4: Creación de la Ingesta y Base en Memoria (`backend/app/services/ingest.py`)
1. Declarar los diccionarios globales `IN_MEMORY_DB` y `TASK_STATUS`.
2. Escribir la función `run_ingest_pipeline` que coordine el parsing y el chunking según el perfil, guardando el resultado final.

### Paso 5: Implementación de Endpoints y Registro de Rutas
1. Crear `backend/app/api/v1/endpoints/documents.py` con las rutas de subida, estado y recuperación de chunks.
2. Modificar `backend/app/api/v1/router.py` para registrar el nuevo router de documentos.

### Paso 6: Suite de Pruebas Integradas (`backend/tests/test_documents.py`)
1. Crear una prueba que genere dinámicamente un PDF mock con PyMuPDF (escribiendo texto en un par de páginas).
2. Subir el PDF mock a `POST /upload`.
3. Consultar el estado hasta completar.
4. Recuperar los chunks y validar que los metadatos `page_number`, `pages` y `char_start` / `char_end` se calculen correctamente.

### Paso 7: Validación de Calidad
1. Ejecutar `uv run ruff check --fix .` y `uv run ruff format .`.
2. Validar todas las pruebas con `uv run pytest`.

---

## 2. Plan de Asignación y Paralelización
Al igual que en la Spec 1, la complejidad técnica es baja y secuencial, por lo que todo el código será implementado en un único hilo de ejecución.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Tras recibir la aprobación del usuario para este Plan de Implementación:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Comenzaremos la codificación paso a paso.
