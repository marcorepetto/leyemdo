# Formulario de Requisitos: Spec 3 - Base de Datos Vectorial Local

Este formulario tiene como objetivo definir el alcance, comportamiento y decisiones técnicas clave para la **Spec 3: Base de Datos Vectorial Local**, encargado de la persistencia de los documentos, fragmentos y sus correspondientes vectores de embeddings.

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para iniciar la fase de definición.

---

## 1. Selección de Base de Datos
* **1.1. ¿Qué motor de base de datos vectorial local prefieres utilizar?**
  * [x] `LanceDB` (Recomendado): Base de datos embebida (serverless), ultrarrápida, se almacena localmente en formato Parquet, muy fácil de instalar y mantener en Python sin necesidad de dockerizar servicios de base de datos externos.
  * [ ] `SQLite-vec`: Extensión de SQLite para búsqueda vectorial, extremadamente ligera, pero requiere la instalación y compilación de la extensión según el sistema operativo.
  * [ ] Otra (especificar): 

---

## 2. Estrategia de Persistencia
* **2.1. ¿Cómo estructuraremos el almacenamiento de la base de datos?**
  * [x] **LanceDB Unificado (Recomendado):** Guardaremos tanto las tablas de metadatos de documentos como las tablas de fragmentos vectoriales directamente en LanceDB (ya que es multi-modal y soporta consultas relacionales y estructuradas sobre columnas estándar).
  * [ ] **Híbrido SQLite + LanceDB:** Usaremos SQLite tradicional (con SQLAlchemy/SQLModel) para los metadatos relacionales de los documentos (historial, etiquetas, progreso de lectura) y LanceDB únicamente para almacenar los vectores y el texto de los chunks.

---

## 3. Modelo de Datos y Esquemas
* **3.1. Confirmación de las Tablas Iniciales:**
  * **Tabla `documents`:**
    * `document_id` (str, hash SHA-256) - Clave primaria.
    * `filename` (str) - Nombre del archivo.
    * `pages_count` (int) - Número de páginas.
    * `total_chars` (int) - Cantidad total de caracteres.
    * `added_at` (datetime) - Fecha de adición.
    * `tags` (list[str]) - Etiquetas del documento.
    * `reading_progress` (float) - Porcentaje de lectura (0.0 a 100.0).
  * **Tabla `chunks`:**
    * `chunk_id` (str, document_id + index) - Clave primaria.
    * `document_id` (str) - Clave foránea.
    * `text` (str) - Contenido del fragmento.
    * `page_number` (int) - Página de inicio.
    * `pages` (list[int]) - Lista de páginas que abarca.
    * `char_start` / `char_end` (int) - Offsets en la página.
    * `section` (str, opcional) - Nombre de la sección.
    * `vector` (vector de floats) - Embedding del fragmento.
  * *¿Estás de acuerdo con este esquema inicial o deseas agregar/quitar campos?* R: Estoy de acuerdo.

---

## 4. Dimensión y Generador de Embeddings Mock
* **4.1. ¿Qué dimensión y mock de embeddings configuraremos?**
  * *Dado que la conexión real con Gemini se implementará en la Spec 4, para probar el funcionamiento de la base de datos crearemos un generador Mock de vectores.*
  * [x] **Mock de 768 Dimensiones (Recomendado):** Es la dimensión nativa del modelo `text-embedding-004` de Google Gemini. Esto facilitará una transición transparente en la Spec 4.
  * [ ] Otra dimensión (especificar): 

---

## 5. Operaciones de Base de Datos Necesarias
* **5.1. Confirmación de los Endpoints mínimos de Base de Datos a exponer:**
  * `GET /api/v1/library/documents`: Listar todos los documentos de la biblioteca (para la vista de tabla).
  * `DELETE /api/v1/library/documents/{document_id}`: Eliminar un documento y todos sus chunks de la base de datos vectorial.
  * `GET /api/v1/library/search`: Realizar una consulta de búsqueda semántica (retorna los chunks más cercanos a una consulta de texto, simulando el motor RAG usando el generador de embeddings mock).
  * *¿Necesitamos algún otro endpoint en esta spec?* R: No, esos están bien por ahora.