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


def parse_pdf(file_bytes: bytes) -> list[dict]:
    """Abre el PDF en memoria, extrae el texto de forma ordenada por columnas,

    aplica limpieza de texto y retorna una lista de páginas estructuradas.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        # sort=True es crucial para procesar layouts de doble columna de forma ordenada
        raw_text = page.get_text("text", sort=True)
        cleaned_text = clean_extracted_text(raw_text)

        pages.append(
            {
                "page_number": i + 1,  # 1-indexed
                "text": cleaned_text,
                "text_len": len(cleaned_text),
            }
        )

    doc.close()
    return pages
