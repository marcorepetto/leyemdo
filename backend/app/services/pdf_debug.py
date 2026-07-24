import fitz  # PyMuPDF

from app.services.pdf_parser import recursive_xy_cut


def draw_debug_annotations(file_bytes: bytes, page_number: int) -> bytes:
    """Abre el PDF, dibuja bounding boxes de bloques, coordenadas en esquinas y

    el orden secuencial resultante en la página especificada, y retorna la imagen PNG.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    if page_number < 1 or page_number > len(doc):
        doc.close()
        raise ValueError(f"Número de página inválido: {page_number}. El documento tiene {len(doc)} páginas.")

    page = doc[page_number - 1]
    raw_blocks = page.get_text("blocks")

    # Filtrar solo bloques que sean texto (b[6] == 0) y no estén vacíos
    text_blocks = []
    for b in raw_blocks:
        if len(b) > 6 and b[6] == 0 and b[4].strip():
            text_blocks.append(b)

    # Ordenar los bloques usando el algoritmo de Recursive X-Y Cut
    text_blocks = recursive_xy_cut(text_blocks)

    # Dibujar anotaciones sobre la página
    for index, b in enumerate(text_blocks, start=1):
        x0, y0, x1, y1 = b[0], b[1], b[2], b[3]

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
        # Pequeño ajuste para centrar la visualización del texto de un dígito o dos
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
