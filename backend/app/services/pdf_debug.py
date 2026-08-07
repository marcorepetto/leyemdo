import logging
import fitz  # PyMuPDF

from app.services.pdf_parser import parse_pdf

logger = logging.getLogger("pdf-debug")


def decode_font_flags(flags: int) -> list[str]:
    """Decodifica los flags de estilo de fuente en PyMuPDF a etiquetas legibles."""
    attrs = []
    if flags & 1:
        attrs.append("superscript")
    if flags & 2:
        attrs.append("italic")
    if flags & 4:
        attrs.append("serif")
    if flags & 8:
        attrs.append("monospaced")
    if flags & 16:
        attrs.append("bold")
    return attrs


def draw_debug_annotations(file_bytes: bytes, page_number: int) -> bytes:
    """Abre el PDF, obtiene el output estructurado de parse_pdf y dibuja bounding boxes de bloques,

    coordenadas en esquinas y el orden secuencial resultante en la página especificada, y retorna la imagen PNG.
    """
    # 1. Obtener la salida estructurada de la función de parsing
    parsed_pages = parse_pdf(file_bytes)

    if page_number < 1 or page_number > len(parsed_pages):
        raise ValueError(f"Número de página inválido: {page_number}. El documento tiene {len(parsed_pages)} páginas.")

    page_data = parsed_pages[page_number - 1]

    # 2. Abrir el documento para renderizado e inserción de anotaciones
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page = doc[page_number - 1]

    # 3. Dibujar anotaciones sobre la página basadas estrictamente en la salida del parser
    for block in page_data.get("blocks", []):
        index = block["index"]
        x0, y0, x1, y1 = block["bbox"]
        block_no = block["block_no"]
        spans = block.get("spans", [])

        # Loggear los metadatos detallados del bloque y sus spans
        logger.info(
            f"Bloque {index}/{len(page_data['blocks'])} [block_no={block_no}] - bbox: ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})"
        )
        logger.info(f"  Texto completo: {block['text']}")
        
        for span_idx, span in enumerate(spans, start=1):
            text = span.get("text", "").strip()
            if not text:
                continue
            font = span.get("font", "Desconocida")
            size = span.get("size", 0.0)
            color_int = span.get("color", 0)
            r, g, b_val = (color_int >> 16) & 255, (color_int >> 8) & 255, color_int & 255
            color_hex = f"#{r:02X}{g:02X}{b_val:02X}"
            flags = span.get("flags", 0)
            flag_attrs = decode_font_flags(flags)
            flag_str = ", ".join(flag_attrs) if flag_attrs else "ninguno"
            
            logger.info(
                f"    Span {span_idx}: '{text}' | Fuente: {font} | Tamaño: {size:.1f}pt | Color: {color_hex} (RGB: {r},{g},{b_val}) | Flags: {flags} ({flag_str})"
            )

        # 1. Bounding box (Rectángulo rojo)
        rect = fitz.Rect(x0, y0, x1, y1)
        page.draw_rect(rect, color=(1, 0, 0), width=1.5)

        # 2. Coordenadas superior izquierda (x0, y0) en azul
        coord_tl = f"({x0:.1f}, {y0:.1f})"
        page.insert_text(fitz.Point(x0, y0 - 3), coord_tl, fontsize=6, color=(0, 0, 1))

        # 3. Coordenadas inferior derecha (x1, y1) en azul
        coord_br = f"({x1:.1f}, {y1:.1f})"
        page.insert_text(fitz.Point(x1 - 40, y1 + 7), coord_br, fontsize=6, color=(0, 0, 1))

        # 4. Número de ordenación (círculo de fondo + número verde/amarillo)
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        center = fitz.Point(cx, cy)

        # Dibujar círculo de fondo
        page.draw_circle(center, radius=9, color=(0, 0.5, 0), fill=(1, 1, 0.8), width=1.0)

        # Insertar el número secuencial centrado
        text_str = str(index)
        offset_x = 2.5 if len(text_str) == 1 else 5.0
        page.insert_text(
            fitz.Point(cx - offset_x, cy + 3.0),
            text_str,
            fontsize=9,
            color=(0, 0.5, 0),
        )

    # Renderizar la página a PNG de alta resolución (DPI = 150)
    pix = page.get_pixmap(dpi=150)
    png_bytes = pix.tobytes("png")

    doc.close()
    return png_bytes
