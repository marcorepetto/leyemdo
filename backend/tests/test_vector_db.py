import math
from datetime import datetime

import pytest

from app.services.embeddings import MockEmbeddingService
from app.services.vector_db import ChatMessageModel, ChunkModel, DocumentModel, VectorDB


@pytest.mark.anyio
async def test_mock_embedding_service():
    service = MockEmbeddingService(dimension=2048)

    text_1 = "This is a test document about machine learning."
    text_2 = "This is a test document about machine learning."
    text_3 = "Different text content."

    vec_1 = await service.get_query_embedding(text_1)
    vec_2 = await service.get_query_embedding(text_2)
    vec_3 = await service.get_query_embedding(text_3)

    # Check dimension
    assert len(vec_1) == 2048
    assert len(vec_3) == 2048

    # Check determinism
    assert vec_1 == vec_2
    assert vec_1 != vec_3

    # Check normalization
    norm = math.sqrt(sum(x * x for x in vec_1))
    assert math.isclose(norm, 1.0, rel_tol=1e-5)

    # Check list embeddings
    list_vecs = await service.get_embeddings([text_1, text_3])
    assert len(list_vecs) == 2
    assert list_vecs[0] == vec_1
    assert list_vecs[1] == vec_3


@pytest.mark.anyio
async def test_vector_db_operations(client):
    VectorDB.init_db()

    doc_id = "test_doc_hash_123"

    # Create sample document metadata
    doc = DocumentModel(
        document_id=doc_id,
        filename="academic_paper.pdf",
        pages_count=2,
        total_chars=1200,
        added_at=datetime.utcnow(),
        tags=["academic", "test"],
        reading_progress=0.0,
    )

    # Create sample chunks
    service = MockEmbeddingService(dimension=2048)
    text_c1 = "This is chunk number one of the document."
    text_c2 = "And here is the second chunk of our document."

    chunks = [
        ChunkModel(
            chunk_id=f"{doc_id}_0",
            document_id=doc_id,
            text=text_c1,
            page_number=1,
            pages=[1],
            char_start=0,
            char_end=len(text_c1),
            section="Introduction",
            vector=await service.get_query_embedding(text_c1),
        ),
        ChunkModel(
            chunk_id=f"{doc_id}_1",
            document_id=doc_id,
            text=text_c2,
            page_number=2,
            pages=[1, 2],
            char_start=len(text_c1) + 1,
            char_end=len(text_c1) + 1 + len(text_c2),
            section="Methodology",
            vector=await service.get_query_embedding(text_c2),
        ),
    ]

    # Add to database
    VectorDB.add_document(doc, chunks)

    # Retrieve documents
    docs = VectorDB.get_documents()
    assert len(docs) > 0

    found_doc = None
    for d in docs:
        if d["document_id"] == doc_id:
            found_doc = d
            break

    assert found_doc is not None
    assert found_doc["filename"] == "academic_paper.pdf"
    assert found_doc["chunks_count"] == 2

    # Retrieve chunks
    db_chunks = VectorDB.get_document_chunks(doc_id)
    assert len(db_chunks) == 2
    assert db_chunks[0]["text"] == text_c1

    # Test semantic search
    query_vector = await service.get_query_embedding(text_c1)
    search_results = VectorDB.search_chunks(query_vector, limit=5)

    assert len(search_results) > 0
    best_match = search_results[0]
    assert best_match["document_id"] == doc_id
    assert best_match["chunk_id"] == f"{doc_id}_0"
    assert math.isclose(best_match["score"], 1.0, abs_tol=1e-4)


@pytest.mark.anyio
async def test_chat_messages_operations(client):
    VectorDB.init_db()

    doc_id = "chat_test_doc_123"

    # Create chat messages
    msg1 = ChatMessageModel(
        message_id="msg_1",
        document_id=doc_id,
        role="user",
        content="What is this document about?",
        timestamp=datetime.utcnow(),
    )

    msg2 = ChatMessageModel(
        message_id="msg_2",
        document_id=doc_id,
        role="assistant",
        content="It is a paper about AI.",
        timestamp=datetime.utcnow(),
        reasoning_details="Reading content...",
    )

    # Save chat messages
    VectorDB.add_chat_messages([msg1, msg2])

    # Retrieve chat history
    history = VectorDB.get_chat_history(doc_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[1]["reasoning_details"] == "Reading content..."

    # Clear history
    VectorDB.clear_chat_history(doc_id)
    history_after = VectorDB.get_chat_history(doc_id)
    assert len(history_after) == 0
