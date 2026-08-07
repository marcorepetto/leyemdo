import io
from unittest.mock import patch

import fitz
from fastapi import status
from app.services.metadata_extractor import PaperMetadata


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

    # 5. Validar listado en biblioteca (GET /api/v1/library/documents)
    library_response = client.get("/api/v1/library/documents")
    assert library_response.status_code == status.HTTP_200_OK
    library_docs = library_response.json()
    assert len(library_docs) > 0
    library_doc = next((d for d in library_docs if d["document_id"] == document_id), None)
    assert library_doc is not None
    assert library_doc["filename"] == "mock_paper.pdf"
    assert library_doc["chunks_count"] > 0

    # 6. Validar búsqueda semántica (GET /api/v1/library/search)
    query_text = chunks[0]["text"]
    search_response = client.get("/api/v1/library/search", params={"q": query_text, "limit": 2})
    assert search_response.status_code == status.HTTP_200_OK
    search_results = search_response.json()
    assert len(search_results) > 0
    assert search_results[0]["document_id"] == document_id
    assert search_results[0]["text"] == query_text

    # 7. Validar borrado de biblioteca (DELETE /api/v1/library/documents/{document_id})
    delete_response = client.delete(f"/api/v1/library/documents/{document_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["status"] == "success"

    # Verificar que ya no está en la biblioteca
    library_response_post = client.get("/api/v1/library/documents")
    assert library_response_post.status_code == status.HTTP_200_OK
    library_docs_post = library_response_post.json()
    assert not any(d["document_id"] == document_id for d in library_docs_post)

    # Verificar que tampoco se pueden recuperar sus chunks
    chunks_response_post = client.get(f"/api/v1/documents/chunks/{document_id}")
    assert chunks_response_post.status_code == status.HTTP_404_NOT_FOUND


@patch("app.api.v1.endpoints.documents.extract_paper_metadata")
def test_extract_metadata_endpoint(mock_extract, client):
    mock_extract.return_value = PaperMetadata(
        title="Mock Title For Testing Endpoint",
        authors=["Alice", "Bob"],
        journal="Journal of Testing",
        year=2026,
        doi="10.1234/test.123",
        abstract="Mock abstract for test.",
        extraction_source="doi"
    )
    
    pdf_data = create_mock_pdf()
    file_like = io.BytesIO(pdf_data)
    
    response = client.post(
        "/api/v1/documents/extract-metadata",
        files={"file": ("mock_paper.pdf", file_like, "application/pdf")},
    )
    
    assert response.status_code == status.HTTP_200_OK
    res_data = response.json()
    assert res_data["title"] == "Mock Title For Testing Endpoint"
    assert res_data["authors"] == ["Alice", "Bob"]
    assert res_data["extraction_source"] == "doi"
