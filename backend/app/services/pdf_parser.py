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


class interval:
    """Clase auxiliar para representar un intervalo 1D (horizontal o vertical) y detectar solapamientos."""

    def __init__(self, start: float, end: float, axis: int = 0):
        self.start = start
        self.end = end
        self.axis = axis  # 0 para horizontal (X), 1 para vertical (Y)

    def __len__(self):
        return self.end - self.start

    def overlap(self, other, tolerance: float = 0.0) -> bool:
        if self.end <= other.start + tolerance:
            return False

        self.end = max(self.end, other.end)
        return True

    def separation(self, other) -> float:
        """Calcula la separación entre dos intervalos. Retorna 0 si se solapan."""
        if self.end <= other.start:
            return other.start - self.end
        elif other.end <= self.start:
            return self.start - other.end
        else:
            return 0.0  # Se solapan


def sort_blocks(blocks: list) -> list:
    def compare_fallback(a, b) -> int:
        # Revisar overlap
        y_diff = a[1] - b[1]
        height_a = a[3] - a[1]
        height_b = b[3] - b[1]
        y_diff = y_diff / max(height_a, height_b, 1.0)  # Normalizar por altura para tolerancia relativa

        x_diff = a[0] - b[0]
        width_a = a[2] - a[0]
        width_b = b[2] - b[0]
        x_diff = x_diff / max(width_a, width_b, 1.0)  # Normalizar por ancho para tolerancia relativa

        if abs(y_diff) > abs(x_diff):
            return -1 if y_diff < 0 else 1
        else:
            return -1 if x_diff < 0 else 1

    return sorted(blocks, key=cmp_to_key(compare_fallback))


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

    gaps_x = [
        (current.end, current.separation(next))
        for current, next in zip(x_intervals[:-1], x_intervals[1:], strict=False)
    ]

    if len(x_intervals) > 1:
        # Dividir a partir del final del primer bloque de X detectado
        split_x, _ = max(gaps_x, key=lambda g: g[1])  # Tomar el gap más grande
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

    gaps_y = [
        (current.end, current.separation(next))
        for current, next in zip(y_intervals[:-1], y_intervals[1:], strict=False)
    ]

    if len(y_intervals) > 1:
        # Dividir a partir del final del primer bloque de Y detectado
        split_y, _ = max(gaps_y, key=lambda g: g[1])  # Tomar el gap más grande
        above = [b for b in blocks if b[3] <= split_y + 1.0]
        below = [b for b in blocks if b[1] >= split_y - 1.0]

        # Validar partición limpia no-vacía
        if above and below and len(above) + len(below) == len(blocks):
            return recursive_xy_cut(above) + recursive_xy_cut(below)

    # 3. Si no hay cortes geométricos limpios, ordenamos por y0 (arriba a abajo) y luego x0 (izquierda a derecha)
    return sort_blocks(blocks)


def filter_nested_blocks(blocks: list) -> list:
    """Elimina bloques que están contenidos de forma casi completa (solapamiento > 90% del área del menor)

    dentro de otros bloques mayores. Esto resuelve duplicaciones y anidamientos de PyMuPDF.
    """
    to_remove = set()
    for i, a in enumerate(blocks):
        w_a = a[2] - a[0]
        h_a = a[3] - a[1]
        area_a = w_a * h_a
        if area_a <= 0:
            to_remove.add(i)
            continue

        for j, b in enumerate(blocks):
            if i == j:
                continue

            w_b = b[2] - b[0]
            h_b = b[3] - b[1]
            area_b = w_b * h_b

            # Si el bloque b es más pequeño o igual, no puede contener a 'a'
            if area_b <= area_a:
                continue

            # Calcular intersección
            ix0 = max(a[0], b[0])
            iy0 = max(a[1], b[1])
            ix1 = min(a[2], b[2])
            iy1 = min(a[3], b[3])

            if ix1 > ix0 and iy1 > iy0:
                inter_area = (ix1 - ix0) * (iy1 - iy0)
                # Si el 90% o más de 'a' está dentro de 'b'
                if inter_area >= 0.8 * area_a:
                    to_remove.add(i)
                    break

    return [b for i, b in enumerate(blocks) if i not in to_remove]


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

    # Eliminar bloques contenidos dentro de otros bloques mayores para evitar duplicaciones
    clean_blocks = filter_nested_blocks(text_blocks)

    # Ordenar los bloques usando el algoritmo de Recursive X-Y Cut
    ordered_blocks = recursive_xy_cut(clean_blocks)

    # Concatenar el texto de los bloques ordenados usando doble salto de línea
    return "\n\n".join(b[4].strip() for b in ordered_blocks)


def _remove_arxiv_block(pages: list[dict]) -> None:
    """Elimina de la página 1 cualquier bloque cuyo texto comience con 'arXiv:XXXX.XXXXX'."""
    if not pages:
        return

    first_page = pages[0]
    arxiv_pattern = re.compile(r"^arXiv:\d{4}\.\d{4,5}")
    first_page["blocks"] = [
        b for b in first_page["blocks"] if not arxiv_pattern.match(b["text"])
    ]


def _remove_repeating_edge_blocks(pages: list[dict]) -> None:
    """Elimina bloques repetidos en los bordes de cada página (headers y footers).

    Detecta si el primer o último bloque de texto se repite de forma consistente
    desde la página 1 o 2 en adelante. Si se repite en todas las páginas del rango,
    lo elimina de cada una.
    """
    if len(pages) < 2:
        return

    for position in ("first", "last"):
        for start_page_idx in (0, 1):
            if start_page_idx >= len(pages):
                continue

            # Obtener el texto de referencia del bloque en la posición indicada
            ref_blocks = pages[start_page_idx]["blocks"]
            if not ref_blocks:
                continue

            ref_text = (
                ref_blocks[0]["text"] if position == "first" else ref_blocks[-1]["text"]
            )

            # Verificar que se repite en TODAS las páginas desde start_page_idx
            repeats = True
            for p in pages[start_page_idx:]:
                if not p["blocks"]:
                    repeats = False
                    break
                edge_text = (
                    p["blocks"][0]["text"]
                    if position == "first"
                    else p["blocks"][-1]["text"]
                )
                if edge_text != ref_text:
                    repeats = False
                    break

            if repeats:
                # Eliminar el bloque repetido de cada página en el rango
                for p in pages[start_page_idx:]:
                    if not p["blocks"]:
                        continue
                    if position == "first":
                        p["blocks"] = p["blocks"][1:]
                    else:
                        p["blocks"] = p["blocks"][:-1]
                break  # Ya encontramos repetición desde este start_page_idx, no probar el otro


def _rebuild_page_text(pages: list[dict]) -> None:
    """Reconstruye el campo 'text' y 'text_len' de cada página a partir de sus bloques."""
    for p in pages:
        ordered_text = "\n\n".join(b["text"] for b in p["blocks"])
        cleaned = clean_extracted_text(ordered_text)
        p["text"] = cleaned
        p["text_len"] = len(cleaned)


def parse_pdf(file_bytes: bytes) -> list[dict]:
    """Abre el PDF en memoria, extrae el texto ordenando los bloques por lectura natural 2D,
    aplica la limpieza de texto y retorna la estructura de páginas.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        # Obtener las dimensiones de la página
        rect = page.rect
        width = rect.width
        height = rect.height

        # Obtener los bloques estructurados de la página
        raw_blocks = page.get_text("blocks")

        # Extraer la estructura detallada con spans (fuente, tamaño, color, flags)
        page_dict = page.get_text("dict")
        spans_by_block = {}
        for block in page_dict.get("blocks", []):
            if block.get("type") == 0:  # Bloque de texto
                block_no = block.get("number")
                spans_list = []
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        spans_list.append({
                            "text": span.get("text", ""),
                            "font": span.get("font", ""),
                            "size": span.get("size", 0.0),
                            "color": span.get("color", 0),
                            "flags": span.get("flags", 0),
                            "bbox": list(span.get("bbox", (0.0, 0.0, 0.0, 0.0)))
                        })
                spans_by_block[block_no] = spans_list

        # Filtrar solo bloques que sean texto (b[6] == 0) y no estén vacíos
        text_blocks = []
        for b in raw_blocks:
            if len(b) > 6 and b[6] == 0 and b[4].strip():
                text_blocks.append(b)

        # Eliminar bloques contenidos dentro de otros bloques mayores
        clean_blocks = filter_nested_blocks(text_blocks)

        # Ordenar los bloques usando el algoritmo de Recursive X-Y Cut
        ordered_blocks = recursive_xy_cut(clean_blocks)

        # Formatear la lista de bloques con su información
        formatted_blocks = []
        for idx, b in enumerate(ordered_blocks, start=1):
            x0, y0, x1, y1 = b[0], b[1], b[2], b[3]
            block_no = b[5]
            spans = spans_by_block.get(block_no, [])
            formatted_blocks.append({
                "index": idx,
                "bbox": [x0, y0, x1, y1],
                "block_no": block_no,
                "text": b[4].strip(),
                "spans": spans
            })

        pages.append(
            {
                "page_number": i + 1,
                "width": width,
                "height": height,
                "blocks": formatted_blocks,
            }
        )

    doc.close()

    # Post-procesamiento: eliminar bloques no deseados
    _remove_arxiv_block(pages)
    _remove_repeating_edge_blocks(pages)

    # Reconstruir texto y reindexar bloques tras las eliminaciones
    for p in pages:
        for idx, b in enumerate(p["blocks"], start=1):
            b["index"] = idx

    _rebuild_page_text(pages)

    return pages
