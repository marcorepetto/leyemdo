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


def sort_blocks_by_columns(blocks: list) -> str:
    """Ordena los bloques de texto de una página identificando columnas y barras

    laterales (layouts multi-columna) para evitar que se mezclen textos paralelos.
    """
    # Filtrar solo bloques que sean texto (b[6] == 0) y no estén vacíos
    text_blocks = []
    for b in blocks:
        # Estructura del bloque: (x0, y0, x1, y1, "texto", block_no, block_type)
        if len(b) > 6 and b[6] == 0 and b[4].strip():
            text_blocks.append(b)

    if not text_blocks:
        return ""

    # Ordenar los bloques inicialmente por su coordenada horizontal izquierda (x0)
    text_blocks.sort(key=lambda x: x[0])

    columns = []
    current_col = [text_blocks[0]]
    threshold = 50.0  # Tolerancia en puntos (PDF points) para separar columnas

    for b in text_blocks[1:]:
        # Comparar con el inicio horizontal mínimo de la columna actual
        min_x0 = min(col_b[0] for col_b in current_col)
        if abs(b[0] - min_x0) < threshold:
            current_col.append(b)
        else:
            columns.append(current_col)
            current_col = [b]
    columns.append(current_col)

    # Ordenar las columnas de izquierda a derecha (usando el promedio x0 de sus bloques)
    columns.sort(key=lambda col: sum(b[0] for b in col) / len(col))

    sorted_blocks = []
    for col in columns:
        # Ordenar los bloques dentro de cada columna de arriba a abajo (coordenada y0)
        col.sort(key=lambda x: x[1])
        sorted_blocks.extend(col)

    # Concatenar el texto de los bloques ordenados usando doble salto de línea
    return "\n\n".join(b[4].strip() for b in sorted_blocks)


def parse_pdf(file_bytes: bytes) -> list[dict]:
    """Abre el PDF en memoria, extrae el texto agrupándolo por columnas y barras laterales,

    aplica la limpieza de texto y retorna la estructura de páginas.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        # Obtener los bloques estructurados de la página
        raw_blocks = page.get_text("blocks")

        # Ordenar los bloques por columnas para evitar la mezcla de la barra lateral con el contenido principal
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
