import re


def detect_section(text: str) -> str | None:
    """Heurística simple para detectar si el fragmento comienza con o contiene el

    título de una sección.
    """
    lines = text.split("\n")
    # Inspeccionar las primeras 3 líneas del fragmento
    for line in lines[:3]:
        line = line.strip()

        # Coincide con secciones numeradas o títulos estándar (ej. "1. Introduction", "Abstract", "REFERENCES")
        match = re.match(r"^((?:[0-9]+(?:\.[0-9]+)*\.?\s+)?[A-Z][A-Za-z\s]{2,30})$", line)
        if match:
            return match.group(1).strip()

        # Coincide con títulos todo en mayúsculas (ej. "ABSTRACT", "CONCLUSIONS")
        if line.isupper() and 3 < len(line) < 30:
            return line

    return None


def split_text_recursively(
    text: str,
    start_offset: int,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
) -> list[tuple[str, int, int]]:
    """Divide recursivamente el texto manteniendo el rastreo de offsets de caracteres."""
    if len(text) <= chunk_size:
        return [(text, start_offset, start_offset + len(text))]

    # Seleccionar separador actual
    separator = separators[0]
    next_separators = separators[1:] if len(separators) > 1 else separators

    # Dividir el texto en partes
    parts = []
    if separator == "":
        # División por caracteres
        for i in range(len(text)):
            parts.append((text[i], start_offset + i))
    else:
        last_idx = 0
        # Buscar todas las apariciones del separador
        for match in re.finditer(re.escape(separator), text):
            part = text[last_idx : match.start()]
            if part:
                parts.append((part, start_offset + last_idx))
            last_idx = match.end()
        part = text[last_idx:]
        if part:
            parts.append((part, start_offset + last_idx))

    # Agrupar partes en chunks
    chunks = []
    current_chunk_parts = []
    current_chunk_len = 0

    for part_text, part_start in parts:
        part_len = len(part_text)

        # Si una sola parte supera el tamaño máximo, se divide recursivamente
        if part_len > chunk_size:
            if current_chunk_parts:
                c_start = current_chunk_parts[0][1]
                c_end = current_chunk_parts[-1][1] + len(current_chunk_parts[-1][0])
                c_text = text[c_start - start_offset : c_end - start_offset]
                chunks.append((c_text, c_start, c_end))
                current_chunk_parts = []
                current_chunk_len = 0

            sub_chunks = split_text_recursively(part_text, part_start, chunk_size, chunk_overlap, next_separators)
            chunks.extend(sub_chunks)
            continue

        if current_chunk_len + part_len <= chunk_size:
            current_chunk_parts.append((part_text, part_start))
            current_chunk_len += part_len
        else:
            if current_chunk_parts:
                c_start = current_chunk_parts[0][1]
                c_end = current_chunk_parts[-1][1] + len(current_chunk_parts[-1][0])
                c_text = text[c_start - start_offset : c_end - start_offset]
                chunks.append((c_text, c_start, c_end))

            # Calcular solapamiento para el siguiente fragmento
            overlap_parts = []
            overlap_len = 0
            for p_text, p_start in reversed(current_chunk_parts):
                if overlap_len + len(p_text) <= chunk_overlap:
                    overlap_parts.insert(0, (p_text, p_start))
                    overlap_len += len(p_text)
                else:
                    break

            current_chunk_parts = overlap_parts + [(part_text, part_start)]
            current_chunk_len = overlap_len + part_len

    if current_chunk_parts:
        c_start = current_chunk_parts[0][1]
        c_end = current_chunk_parts[-1][1] + len(current_chunk_parts[-1][0])
        c_text = text[c_start - start_offset : c_end - start_offset]
        chunks.append((c_text, c_start, c_end))

    return chunks


def split_document(
    pages: list[dict],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[dict]:
    """Segmenta todo el texto del documento de forma continua y calcula a qué páginas

    corresponde cada fragmento.
    """
    # 1. Concatenar texto y registrar los límites de caracteres por página
    full_text = ""
    page_boundaries = []
    current_offset = 0

    for page in pages:
        start_idx = current_offset
        end_idx = current_offset + page["text_len"]
        page_boundaries.append(
            {
                "page_number": page["page_number"],
                "start": start_idx,
                "end": end_idx,
            }
        )
        full_text += page["text"] + "\n"
        current_offset += page["text_len"] + 1

    # 2. Segmentar recursivamente el flujo de texto completo
    separators = ["\n\n", "\n", " ", ""]
    raw_chunks = split_text_recursively(full_text, 0, chunk_size, chunk_overlap, separators)

    # 3. Mapear cada chunk con las páginas físicas que cruza
    processed_chunks = []
    for idx, (chunk_text, start, end) in enumerate(raw_chunks):
        # Determinar páginas cruzadas
        overlapped_pages = []
        for boundary in page_boundaries:
            # Hay solapamiento si los rangos [start, end] y [boundary.start, boundary.end] se cruzan
            if start < boundary["end"] and end > boundary["start"]:
                overlapped_pages.append(boundary["page_number"])

        # Si no se detectó página por seguridad, asignar la primera
        if not overlapped_pages:
            overlapped_pages = [1]

        primary_page = overlapped_pages[0]

        # Encontrar el límite de la página primaria para calcular la posición relativa del caracter
        primary_boundary = next(b for b in page_boundaries if b["page_number"] == primary_page)

        char_start = max(0, start - primary_boundary["start"])
        char_end = min(
            primary_boundary["end"] - primary_boundary["start"],
            end - primary_boundary["start"],
        )

        section = detect_section(chunk_text)

        processed_chunks.append(
            {
                "chunk_index": idx,
                "text": chunk_text.strip(),
                "page_number": primary_page,
                "pages": overlapped_pages,
                "char_start": char_start,
                "char_end": char_end,
                "section": section,
            }
        )

    return processed_chunks
