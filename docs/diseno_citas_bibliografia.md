# Diseño Técnico: Extracción y Parseo de Citas y Bibliografía

Este documento detalla el diseño propuesto para la extracción automática de citas inline y la sección de bibliografía en los papers PDF, con el fin de habilitar referencias cruzadas e interactividad en fases futuras del desarrollo.

---

## 1. Valor Aportado e Integración

El parseo de la estructura bibliográfica del documento alimenta dos funcionalidades clave de la aplicación:
1. **Chat Lateral (Spec 8):** Permite que, al hacer clic en una cita (ej. `[3]`) dentro de las respuestas de la IA, el lector salte a la página exacta de la sección "References" del PDF o muestre un tooltip interactivo con el detalle de la fuente citada.
2. **Biblioteca de Grafo Semántico (Spec 9):** Permite establecer relaciones dirigidas entre documentos de la biblioteca local. Si un paper A cita a un paper B (y ambos están guardados localmente), el grafo los unirá visualmente con una arista.

---

## 2. Estructura de Datos Propuesta

### A. A nivel de Documento (Metadatos Globales)
Añadir un mapa clave-valor que asocie cada índice de referencia con su descripción textual completa:
```json
{
  "document_id": "sha256_hash",
  "pages_count": 12,
  "bibliography": {
    "1": "Zhou, M., et al. Applications of Voronoi Diagrams in Multi-Robot Coverage. J. Mar. Sci. Eng. 2024.",
    "2": "Ridolfi, A. Coordination strategies for multi-robot systems. Rob. Auton. Syst. 2023.",
    "3": "Author, C. Title of another paper. Journal Name. 2022."
  }
}
```

### B. A nivel de Fragmento (Chunk Metadata)
Añadir una lista que registre los identificadores de citas que aparecen dentro del texto del chunk:
```json
{
  "chunk_index": 4,
  "text": "Among them, some studies have focused on the overall conceptual framework [1]. An in-depth discussion on the relationship between humans and robots is proposed in [2]...",
  "page_number": 1,
  "pages": [1],
  "citations": ["1", "2"]
}
```

---

## 3. Algoritmo y Lógica de Extracción (Propuesta de Implementación)

### Paso 1: Extracción de la sección de Bibliografía
1. **Identificar inicio:** Buscar la sección final del texto del documento que coincida con títulos como `"References"`, `"Bibliography"`, `"Bibliografía"` o `"Referencias"`.
2. **Parsear cada entrada:** Utilizar expresiones regulares sobre las líneas de esta sección para extraer el número de referencia y el contenido.
   * **Regex sugerido:** `r'^\s*\[?([0-9]+)\]?\.?\s+(.+)$'`
   * Permite capturar tanto formatos tipo `[1] Autor...` como `1. Autor...`.

### Paso 2: Escaneo de Citas Inline por Chunk
1. Escanear el texto del chunk utilizando una expresión regular para buscar corchetes con números, comas o guiones.
   * **Regex sugerido:** `r'\[([0-9\s,\-]+)\]'`
2. **Procesar el contenido capturado:**
   * Si es un número simple (`"1"`): Añadir `"1"`.
   * Si es una lista separada por comas (`"1, 2, 5"`): Dividir y añadir `["1", "2", "5"]`.
   * Si es un rango con guión (`"5-8"`): Expandir el rango numérico y añadir `["5", "6", "7", "8"]`.
