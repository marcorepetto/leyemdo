import io

import fitz
from fastapi import status


def create_mock_pdf() -> bytes:
    """Genera dinámicamente un archivo PDF de dos páginas en memoria usando PyMuPDF."""
    doc = fitz.open()

    # Página 1
    page1 = doc.new_page()
    page1.insert_text(
        (50, 50),
        "This is the first page of the mock academic paper.\n"
        "1. Introduction\n"
        "We present our findings about artificial intelligence in this first section. "
        "It spans some length to verify splitting.",
    )

    # Página 2
    page2 = doc.new_page()
    page2.insert_text(
        (50, 50),
        "This is the second page of the paper. We continue here.\n"
        "References\n"
        "This is the reference section of our paper.",
    )

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def test_upload_and_ingest_pipeline(client):
    # 1. Generar el PDF mock
    pdf_data = create_mock_pdf()
    file_like = io.BytesIO(pdf_data)

    # 2. Subir el documento a la API
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("mock_paper.pdf", file_like, "application/pdf")},
        params={"profile": "paper", "chunk_size": 80, "chunk_overlap": 20},
    )

    # Dado que es TestClient, las BackgroundTasks de FastAPI se ejecutan síncronamente
    # dentro de la misma llamada.
    assert response.status_code == status.HTTP_202_ACCEPTED
    res_data = response.json()
    assert "task_id" in res_data
    assert "document_id" in res_data
    assert res_data["status"] in ("processing", "completed")

    task_id = res_data["task_id"]
    document_id = res_data["document_id"]

    # 3. Validar estado de la tarea
    status_response = client.get(f"/api/v1/documents/status/{task_id}")
    assert status_response.status_code == status.HTTP_200_OK
    status_data = status_response.json()
    assert status_data["status"] == "completed"

    # 4. Validar los chunks generados
    chunks_response = client.get(f"/api/v1/documents/chunks/{document_id}")
    assert chunks_response.status_code == status.HTTP_200_OK
    chunks_data = chunks_response.json()

    assert chunks_data["document_id"] == document_id
    assert chunks_data["pages_count"] == 2
    assert chunks_data["total_chars"] > 0

    chunks = chunks_data["chunks"]
    assert len(chunks) > 0

    # Validar la estructura y metadatos de los chunks
    for chunk in chunks:
        assert "chunk_index" in chunk
        assert "text" in chunk
        assert "page_number" in chunk
        assert isinstance(chunk["pages"], list)
        assert "char_start" in chunk
        assert "char_end" in chunk
        assert "section" in chunk

    # Validar que al menos un chunk detectó una sección (como "1. Introduction" o "References")
    sections_detected = [c["section"] for c in chunks if c["section"] is not None]
    assert len(sections_detected) > 0
    assert any("Introduction" in s or "References" in s for s in sections_detected)
