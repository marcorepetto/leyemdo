# Plan Técnico: Spec - Debug PDF Parser

Este plan técnico detalla los archivos a crear y modificar, la lógica de dibujo de anotaciones mediante la API de PyMuPDF y el diseño de la interfaz web responsiva para la depuración del parser.

---

## 1. Archivos Impactados y Creados

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── debug.py        <-- NUEVO: Endpoints de depuración (upload, view PNG, UI HTML)
│   │       │   └── documents.py
│   │       └── router.py           <-- MODIFICADO: Registro del router de depuración
│   ├── services/
│   │   ├── __init__.py
│   │   └── pdf_debug.py            <-- NUEVO: Utilidad de anotación y dibujo en PDF (PyMuPDF)
│   └── ...
└── ...
```

---

## 2. Detalle de Diseño e Implementación

### A. Servicio de Anotación y Dibujo (`backend/app/services/pdf_debug.py`)
Implementaremos la función `draw_debug_annotations(file_bytes: bytes, page_number: int) -> bytes`:
1. Abrir el PDF usando `fitz.open(stream=file_bytes, filetype="pdf")`.
2. Seleccionar la página `page = doc[page_number - 1]`.
3. Obtener bloques de texto mediante `page.get_text("blocks")`.
4. Filtrar los bloques de texto válidos (tipo `0` y no vacíos).
5. Importar y aplicar el comparador `compare_blocks` (del servicio `pdf_parser.py`) para ordenar la lista:
   `text_blocks.sort(key=cmp_to_key(compare_blocks))`.
6. Para cada bloque con su índice (1-indexed):
   * **Caja Delimitadora:** Dibujar un rectángulo rojo:
     `page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=(1, 0, 0), width=1.5)`
   * **Coordenadas:** Insertar en fuente pequeña y color azul:
     * Superior Izquierda `(x0, y0)` en `fitz.Point(x0, y0 - 4)`.
     * Inferior Derecha `(x1, y1)` en `fitz.Point(x1 - 40, y1 + 8)`.
     * Llamada: `page.insert_text(point, text, fontsize=6, color=(0, 0, 1))`.
   * **Número de Ordenación:**
     * Calcular el centro: `cx = (x0 + x1) / 2`, `cy = (y0 + y1) / 2`.
     * Dibujar un círculo con relleno amarillo claro y borde verde como fondo de legibilidad:
       `page.draw_circle(fitz.Point(cx, cy), radius=10, color=(0, 0.5, 0), fill=(1, 1, 0.8), width=1)`
     * Insertar el número centrado:
       `page.insert_text(fitz.Point(cx - 3, cy + 3.5), str(index), fontsize=10, color=(0, 0.5, 0))`
7. Renderizar la página a pixmap de alta resolución (`dpi=150`) y obtener bytes en formato PNG:
   `pix = page.get_pixmap(dpi=150)` -> `pix.tobytes("png")`.
8. Retornar los bytes del PNG.

### B. Endpoints de Depuración (`backend/app/api/v1/endpoints/debug.py`)
* `POST /upload`: Recibe un archivo PDF, calcula su hash SHA-256 y lo guarda en un diccionario en memoria (`DEBUG_PDF_CACHE`).
* `GET /view/{document_id}/page/{page_number}`: Invoca `draw_debug_annotations` y retorna la imagen PNG con `Response(content=png_bytes, media_type="image/png")`.
* `GET /ui`: Retorna `HTMLResponse` con una página web moderna diseñada en HTML/JS que permite:
  * Subir el archivo PDF mediante `fetch` al endpoint `/upload`.
  * Mostrar el visualizador de la imagen de la página.
  * Botones "Anterior" y "Siguiente" con deshabilitación dinámica si se llega a los límites del PDF.
  * Entrada numérica directa de página para salto rápido.

### C. Registro en Enrutador (`backend/app/api/v1/router.py`)
* Registrar el router en la API con el prefijo `/debug`.

---

## 3. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación para este Plan Técnico:
1. Realizaremos un **commit en git** con la planificación aprobada.
2. Escribiremos el **Plan de Implementación** detallando los comandos y orden de creación.
