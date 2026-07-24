from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import status

from app.services.vector_db import ChunkModel, DocumentModel, VectorDB


async def mock_chat_stream(messages):
    yield "Este es "
    yield "un tutor "
    yield "pedagógico."


@pytest.mark.anyio
@patch("app.services.openrouter.OpenRouterService.get_chat_stream", side_effect=mock_chat_stream)
async def test_chat_endpoints_flow(mock_stream, client):
    # 1. Iniciar la BD e insertar un documento de prueba
    VectorDB.init_db()
    doc_id = "chat_integration_doc_999"

    doc = DocumentModel(
        document_id=doc_id,
        filename="test_paper.pdf",
        pages_count=1,
        total_chars=500,
        added_at=datetime.utcnow(),
        tags=["chat-test"],
        reading_progress=0.0,
    )

    # Crear un chunk mock de 2048d
    chunk = ChunkModel(
        chunk_id=f"{doc_id}_0",
        document_id=doc_id,
        text="El teorema de Pitágoras establece que en un triángulo rectángulo...",
        page_number=1,
        pages=[1],
        char_start=0,
        char_end=60,
        section="Matemáticas",
        vector=[0.1] * 2048,
    )

    VectorDB.add_document(doc, [chunk])

    # 2. Enviar mensaje de chat (POST /api/v1/chat/message)
    # Mandamos la consulta
    response = client.post(
        "/api/v1/chat/message", json={"document_id": doc_id, "message": "¿Qué dice el teorema de Pitágoras?"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert "text/event-stream" in response.headers["content-type"]

    # Consumir el stream SSE de respuesta
    content = response.text
    assert "Este es" in content
    assert "un tutor" in content
    assert "pedagógico." in content

    # 3. Validar historial (GET /api/v1/chat/history/{document_id})
    history_response = client.get(f"/api/v1/chat/history/{doc_id}")
    assert history_response.status_code == status.HTTP_200_OK
    history_data = history_response.json()

    assert len(history_data) == 2
    assert history_data[0]["role"] == "user"
    assert history_data[0]["content"] == "¿Qué dice el teorema de Pitágoras?"
    assert history_data[1]["role"] == "assistant"
    assert history_data[1]["content"] == "Este es un tutor pedagógico."

    # 4. Limpiar historial (DELETE /api/v1/chat/history/{document_id})
    clear_response = client.delete(f"/api/v1/chat/history/{doc_id}")
    assert clear_response.status_code == status.HTTP_200_OK
    assert clear_response.json()["status"] == "success"

    # Verificar que el historial quedó vacío
    history_response_post = client.get(f"/api/v1/chat/history/{doc_id}")
    assert history_response_post.status_code == status.HTTP_200_OK
    assert len(history_response_post.json()) == 0
