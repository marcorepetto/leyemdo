# Formulario de Requisitos: Spec 2 - Parsing & Chunking

Este formulario tiene como objetivo definir el alcance, comportamiento y decisiones técnicas clave para la **Spec 2: Parsing & Chunking**, encargado de la extracción de texto y división semántica de los documentos PDF cargados por el usuario.

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para iniciar la fase de definición.

---

## 1. Extracción de Texto de PDF (Parsing)
* **1.1. ¿Qué librería de Python prefieres utilizar para extraer el texto de los PDFs?**
  * [x] `PyMuPDF` (`fitz`): (Recomendada) Extremadamente rápida y proporciona coordenadas precisas de las palabras, lo cual es fundamental para futuros resaltados visuales en el visor.
  * [ ] `pypdf`: Licencia permisiva y ligera, pero con capacidades de coordenadas y renderizado limitadas.
  * [ ] `pdfplumber`: Excelente para extraer tablas y layouts estructurados, pero considerablemente más lenta.
  * [ ] Otra (especificar): 

* **1.2. ¿Se debe realizar algún tipo de limpieza durante el parsing?**
  * *Ejemplos: Eliminar números de página repetitivos, encabezados/pies de página fijos, o normalizar caracteres especiales.*
  * [x] Sí, limpieza básica (quitar dobles espacios, normalizar guiones y saltos de línea).
  * [ ] Sí, intentar omitir headers/footers recurrentes (puede ser propenso a errores en layouts complejos).
  * [ ] No, mantener el texto bruto extraído tal cual.

---

## 2. Estrategia de Segmentación (Chunking)
* **2.1. ¿Qué estrategia de segmentación utilizaremos para dividir el texto?**
  * [x] **Recursive Character Splitter (Recomendado):** Divide el texto buscando saltos de párrafo, luego oraciones y palabras, intentando mantener los fragmentos en un tamaño de token/caracter objetivo con un solapamiento (overlap).
  * [ ] **Semantic Chunking:** Agrupa frases basadas en la similitud semántica de sus embeddings (requiere calcular embeddings de oraciones durante la ingesta, lo que aumenta el tiempo y costo de API).
  * [ ] **Chunking por Página:** Cada fragmento representa exactamente una página física del PDF.

* **2.2. ¿Cuáles serán los límites por defecto del segmentador (en caracteres o tokens)?**
  * *Valores sugeridos:* Tamaño del fragmento = 500-1000 caracteres, Solapamiento (overlap) = 100-200 caracteres.
  * [ ] Confirmar valores sugeridos.
  * [x] Especificar otros: Mi idea inicial es utilizarlo para lectura de papers, en ese caso estimo que esos tamaños son demasiado grandes ¿Podria configurarse en modo libro o paper? ¿En base a que definimos esa cantidad de carácteres?

---

## 3. Metadatos del Fragmento
* **3.1. Además de la página del PDF, ¿qué metadatos debemos adjuntar a cada chunk?**
  * [x] `document_id` (para asociarlo al archivo).
  * [x] `page_number` (crítico para las citas clicables).
  * [x] `char_start` / `char_end` (índices de caracteres en el documento original).
  * [x] `header` / `sección` (si es posible detectarlos con expresiones regulares simples).

---

## 4. API de Ingesta y Procesamiento
* **4.1. ¿Cómo debe manejar el backend la carga y procesamiento de archivos grandes?**
  * [ ] **Síncrono (Simple):** El cliente sube el archivo y la llamada bloquea hasta que el PDF sea procesado por completo (puede expirar en archivos gigantes).
  * [x] **Asíncrono con FastAPI BackgroundTasks (Recomendado):** El cliente sube el archivo, la API guarda el archivo temporalmente, responde de inmediato con `202 Accepted` y procesa el documento en segundo plano sin bloquear.
  * [ ] **Asíncrono con Celery/Redis:** (Complejo, requiere levantar un broker externo).
