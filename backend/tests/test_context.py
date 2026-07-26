from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import status

from app.services.vector_db import ChunkModel, DocumentModel, VectorDB


@pytest.mark.anyio
@patch("app.services.openrouter.OpenRouterService.get_chat_completion")
async def test_explain_endpoint(mock_get_completion, client):
    # Inicializar la base de datos
    VectorDB.init_db()

    doc_id = "test_doc_explain"
    doc = DocumentModel(
        document_id=doc_id,
        filename="test_explain.pdf",
        pages_count=1,
        total_chars=100,
        added_at=datetime.utcnow(),
        tags=["test"],
        reading_progress=0.0,
    )

    # Registrar un fragmento en el documento para que sirva de contexto
    chunk = ChunkModel(
        chunk_id=f"{doc_id}_0",
        document_id=doc_id,
        text="El concepto de diseño responsivo permite adaptar las interfaces a pantallas móviles.",
        page_number=1,
        pages=[1],
        char_start=0,
        char_end=82,
        section="UI",
        vector=[0.1] * 2048,
    )
    VectorDB.add_document(doc, [chunk])

    # Respuesta ficticia de la IA
    mock_get_completion.return_value = "Esta es una explicación simulada de la interfaz responsiva."

    # Petición a /explain
    payload = {"document_id": doc_id, "selected_text": "diseño responsivo"}
    response = client.post("/api/v1/context/explain", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "explanation" in data
    assert data["explanation"] == "Esta es una explicación simulada de la interfaz responsiva."

    mock_get_completion.assert_called_once()


@pytest.mark.anyio
@patch("app.services.openrouter.OpenRouterService.get_chat_completion")
async def test_translate_endpoint(mock_get_completion, client):
    # Inicializar la base de datos
    VectorDB.init_db()

    doc_id = "test_doc_translate"
    doc = DocumentModel(
        document_id=doc_id,
        filename="test_translate.pdf",
        pages_count=1,
        total_chars=100,
        added_at=datetime.utcnow(),
        tags=["test"],
        reading_progress=0.0,
    )
    VectorDB.add_document(doc, [])

    mock_get_completion.return_value = "Responsive design"

    # Petición a /translate
    payload = {"document_id": doc_id, "selected_text": "diseño responsivo", "target_language": "en"}
    response = client.post("/api/v1/context/translate", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "translation" in data
    assert data["translation"] == "Responsive design"

    mock_get_completion.assert_called_once()


@pytest.mark.anyio
async def test_search_related_and_support_endpoints(client):
    # Inicializar la base de datos
    VectorDB.init_db()

    doc_a_id = "doc_a"
    doc_b_id = "doc_b"

    doc_a = DocumentModel(
        document_id=doc_a_id,
        filename="doc_a.pdf",
        pages_count=1,
        total_chars=100,
        added_at=datetime.utcnow(),
    )
    doc_b = DocumentModel(
        document_id=doc_b_id,
        filename="doc_b.pdf",
        pages_count=1,
        total_chars=100,
        added_at=datetime.utcnow(),
    )

    # Crear textos similares
    text_a = "El gato negro saltó sobre la mesa de madera en la cocina."
    text_b = "El felino oscuro brincó arriba del mueble de madera de cocinar."

    from app.services.embeddings import get_embedding_service

    emb_service = get_embedding_service()

    vec_a = await emb_service.get_query_embedding(text_a)
    vec_b = await emb_service.get_query_embedding(text_b)

    chunk_a = ChunkModel(
        chunk_id=f"{doc_a_id}_0",
        document_id=doc_a_id,
        text=text_a,
        page_number=1,
        pages=[1],
        char_start=0,
        char_end=len(text_a),
        section="Mascotas",
        vector=vec_a,
    )
    chunk_b = ChunkModel(
        chunk_id=f"{doc_b_id}_0",
        document_id=doc_b_id,
        text=text_b,
        page_number=1,
        pages=[1],
        char_start=0,
        char_end=len(text_b),
        section="Animales",
        vector=vec_b,
    )

    VectorDB.add_document(doc_a, [chunk_a])
    VectorDB.add_document(doc_b, [chunk_b])

    # 1. Probar endpoint /support para doc A (debería retornar el chunk de A, no de B)
    payload_support = {"document_id": doc_a_id, "selected_text": text_a, "limit": 2}
    response_support = client.post("/api/v1/context/support", json=payload_support)
    assert response_support.status_code == status.HTTP_200_OK
    data_support = response_support.json()

    # Valida que devuelva únicamente el fragmento que pertenece al documento A
    assert len(data_support) == 1
    assert data_support[0]["chunk_id"] == f"{doc_a_id}_0"
    assert data_support[0]["document_id"] == doc_a_id

    # 2. Probar endpoint /search-related para doc A (debería retornar el chunk de B, no de A)
    payload_related = {"document_id": doc_a_id, "selected_text": text_a, "limit": 2}
    response_related = client.post("/api/v1/context/search-related", json=payload_related)
    assert response_related.status_code == status.HTTP_200_OK
    data_related = response_related.json()

    # Valida que excluya el documento de origen y retorne el relacionado de B.
    # Puede haber contaminación de otros documentos de tests previos.
    assert len(data_related) >= 1
    assert any(chunk["chunk_id"] == f"{doc_b_id}_0" for chunk in data_related)
    assert all(chunk["document_id"] != doc_a_id for chunk in data_related)
