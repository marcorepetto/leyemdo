import re
from functools import cmp_to_key

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


def compare_blocks(a, b) -> int:
    """Comparador de orden de lectura en 2D para bloques de PDF.

    Define un orden parcial basado en:
    1. Relación arriba/abajo (si un bloque está completamente sobre el otro).
    2. Relación izquierda/derecha (si los bloques se solapan verticalmente pero
       están separados horizontalmente en columnas).
    """
    # Coordenadas: x0=0, y0=1, x1=2, y1=3
    y_tolerance = 3.0

    # 1. Separación vertical: Si 'a' está completamente arriba de 'b'
    if a[3] <= b[1] + y_tolerance:
        return -1
    # Si 'b' está completamente arriba de 'a'
    if b[3] <= a[1] + y_tolerance:
        return 1

    # 2. Solapamiento vertical significativo: verificar si están en columnas separadas
    overlap_x = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    w_a = a[2] - a[0]
    w_b = b[2] - b[0]
    min_w = min(w_a, w_b)

    # Si el solapamiento horizontal es menor al 10% del ancho del bloque más angosto,
    # se asume que son columnas distintas separadas horizontalmente.
    if overlap_x < 0.1 * min_w:
        # 'a' está a la izquierda de 'b'
        if a[2] <= b[0]:
            return -1
        # 'b' está a la izquierda de 'a'
        if b[2] <= a[0]:
            return 1

    # 3. Si están en la misma columna (o se solapan horizontalmente), ordenar de arriba a abajo
    if a[1] < b[1]:
        return -1
    if b[1] < a[1]:
        return 1

    # 4. Último recurso: de izquierda a derecha
    if a[0] < b[0]:
        return -1
    return 1


def sort_blocks_by_columns(blocks: list) -> str:
    """Ordena los bloques de texto de una página aplicando el comparador 2D de lectura,

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

    # Ordenar los bloques usando el comparador de orden 2D parcial
    text_blocks.sort(key=cmp_to_key(compare_blocks))

    # Concatenar el texto de los bloques ordenados usando doble salto de línea
    return "\n\n".join(b[4].strip() for b in text_blocks)


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
