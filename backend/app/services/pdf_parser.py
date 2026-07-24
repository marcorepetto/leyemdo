import re

import fitz  # PyMuPDF


def clean_extracted_text(text: str) -> str:
    """Limpia el texto extraído del PDF.

    1. Une palabras cortadas por guión al final de la línea.
    2. Normaliza espacios en blanco horizontales.
    3. Reduce saltos de línea redundantes a un máximo de dos (párrafos).
    """
    # Unir palabras cortadas por guiones al final de una línea
    # Ej: "trans-\nformation" -> "transformation"
    text = re.sub(r"(\b\w+)-\s*\n\s*(\w+\b)", r"\1\2", text)

    # Normalizar espacios y tabuladores horizontales sin alterar los saltos de línea
    text = re.sub(r"[ \t]+", " ", text)

    # Reducir saltos de línea excesivos a un máximo de un salto de párrafo (\n\n)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

class interval:
    """Clase auxiliar para representar un intervalo 1D (horizontal o vertical) y detectar solapamientos."""

    def __init__(self, start: float, end: float, axis: int = 0):
        self.start = start
        self.end = end
        self.axis = axis  # 0 para horizontal (X), 1 para vertical (Y)

    def __len__(self):
        return self.end - self.start
    
    def overlap(self, other, tolerance: float = 0.0) -> bool:
        if (self.end <= other.start + tolerance):
            return False 
        
        self.end = max(self.end, other.end)
        return True

def recursive_xy_cut(blocks: list) -> list:
    """Algoritmo de segmentación y ordenación Recursive X-Y Cut para bloques de PDF.

    Divide la página de forma recursiva buscando espacios vacíos (gaps)
    horizontales (Y-cuts) o verticales (X-cuts), reconstruyendo el orden natural
    de lectura en páginas con múltiples columnas, títulos y ecuaciones que las abarcan.
    """
    if len(blocks) <= 1:
        return blocks

    # 2. Intentar encontrar un corte vertical (X-cut)
    # Ordenamos por x0
    sorted_by_x = sorted(blocks, key=lambda b: b[0])
    x_intervals = []
    for b in sorted_by_x:
        x0, x1 = b[0], b[2]
        current = interval(x0, x1, axis=0)
        if not x_intervals:
            x_intervals.append(current)
        else:
            prev = x_intervals[-1]
            # Si se solapan horizontalmente con una tolerancia de 1.0 punto
            if not prev.overlap(current, tolerance=1.0):
                x_intervals.append(current)

    if len(x_intervals) > 1:
        # Dividir a partir del final del primer bloque de X detectado
        split_x = x_intervals[0].end
        left = [b for b in blocks if b[2] <= split_x + 1.0]
        right = [b for b in blocks if b[0] >= split_x - 1.0]

        # Validar partición limpia no-vacía
        if left and right and len(left) + len(right) == len(blocks):
            return recursive_xy_cut(left) + recursive_xy_cut(right)
        
    # 1. Intentar encontrar un corte horizontal (Y-cut)
    # Ordenamos por y0 para agrupar
    sorted_by_y = sorted(blocks, key=lambda b: b[1])
    y_intervals = []
    for b in sorted_by_y:
        y0, y1 = b[1], b[3]
        current = interval(y0, y1, axis=1)
        if not y_intervals:
            y_intervals.append(current)
        else:
            prev = y_intervals[-1]
            # Si se solapan verticalmente con una tolerancia de 1.0 punto
            if not prev.overlap(current, tolerance=1.0):
                y_intervals.append(current)

    if len(y_intervals) > 1:
        # Dividir a partir del final del primer bloque de Y detectado
        split_y = y_intervals[0].end
        above = [b for b in blocks if b[3] <= split_y + 1.0]
        below = [b for b in blocks if b[1] >= split_y - 1.0]

        # Validar partición limpia no-vacía
        if above and below and len(above) + len(below) == len(blocks):
            return recursive_xy_cut(above) + recursive_xy_cut(below)


    # 3. Si no hay cortes geométricos limpios, ordenamos por y0 (arriba a abajo) y luego x0 (izquierda a derecha)
    return sorted(blocks, key=lambda b: (b[0], b[1]))


def sort_blocks_by_columns(blocks: list) -> str:
    """Ordena los bloques de texto de una página aplicando el algoritmo de Recursive X-Y Cut,

    manteniendo de forma correcta el orden de lectura en layouts de doble columna,
    barras laterales y preservando la posición natural de ecuaciones centradas.
    """
    # Filtrar solo bloques que sean texto (b[6] == 0) y no estén vacíos
    text_blocks = []
    for b in blocks:
        # Estructura del bloque: (x0, y0, x1, y1, "texto", block_no, block_type)
        if len(b) > 6 and b[6] == 0 and b[4].strip():
            text_blocks.append(b)

    if not text_blocks:
        return ""

    # Ordenar los bloques usando el algoritmo de Recursive X-Y Cut
    ordered_blocks = recursive_xy_cut(text_blocks)

    # Concatenar el texto de los bloques ordenados usando doble salto de línea
    return "\n\n".join(b[4].strip() for b in ordered_blocks)


def parse_pdf(file_bytes: bytes) -> list[dict]:
    """Abre el PDF en memoria, extrae el texto ordenando los bloques por lectura natural 2D,

    aplica la limpieza de texto y retorna la estructura de páginas.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        # Obtener los bloques estructurados de la página
        raw_blocks = page.get_text("blocks")

        # Ordenar los bloques usando el algoritmo de lectura natural 2D
        ordered_text = sort_blocks_by_columns(raw_blocks)

        cleaned_text = clean_extracted_text(ordered_text)

        pages.append(
            {
                "page_number": i + 1,
                "text": cleaned_text,
                "text_len": len(cleaned_text),
            }
        )

    doc.close()
    return pages
