import math
from datetime import datetime

from app.services.embeddings import MockEmbeddingService
from app.services.vector_db import ChunkModel, DocumentModel, VectorDB


def test_mock_embedding_service():
    service = MockEmbeddingService(dimension=768)

    text_1 = "This is a test document about machine learning."
    text_2 = "This is a test document about machine learning."
    text_3 = "Different text content."

    vec_1 = service.get_query_embedding(text_1)
    vec_2 = service.get_query_embedding(text_2)
    vec_3 = service.get_query_embedding(text_3)

    # Check dimension
    assert len(vec_1) == 768
    assert len(vec_3) == 768

    # Check determinism (identical texts must yield identical vectors)
    assert vec_1 == vec_2
    assert vec_1 != vec_3

    # Check normalization (L2 norm should be very close to 1.0)
    norm = math.sqrt(sum(x * x for x in vec_1))
    assert math.isclose(norm, 1.0, rel_tol=1e-5)

    # Check list embeddings
    list_vecs = service.get_embeddings([text_1, text_3])
    assert len(list_vecs) == 2
    assert list_vecs[0] == vec_1
    assert list_vecs[1] == vec_3


def test_vector_db_operations(client):
    # Ensure database is clean/initialized
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
    service = MockEmbeddingService()
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
            vector=service.get_query_embedding(text_c1),
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
            vector=service.get_query_embedding(text_c2),
        ),
    ]

    # Add to database
    VectorDB.add_document(doc, chunks)

    # Retrieve documents
    docs = VectorDB.get_documents()
    assert len(docs) > 0

    # Verify the specific document exists and chunk count is correct
    found_doc = None
    for d in docs:
        if d["document_id"] == doc_id:
            found_doc = d
            break

    assert found_doc is not None
    assert found_doc["filename"] == "academic_paper.pdf"
    assert found_doc["chunks_count"] == 2
    assert "academic" in found_doc["tags"]

    # Retrieve chunks
    db_chunks = VectorDB.get_document_chunks(doc_id)
    assert len(db_chunks) == 2
    assert db_chunks[0]["text"] == text_c1
    assert db_chunks[1]["text"] == text_c2
    assert db_chunks[0]["page_number"] == 1
    assert db_chunks[1]["pages"] == [1, 2]

    # Test semantic search
    # Searching for identical text to chunk 1 should return chunk 1 with high similarity
    query = text_c1
    query_vector = service.get_query_embedding(query)
    search_results = VectorDB.search_chunks(query_vector, limit=5)

    assert len(search_results) > 0
    # The first result should be chunk 1
    best_match = search_results[0]
    assert best_match["document_id"] == doc_id
    assert best_match["chunk_id"] == f"{doc_id}_0"
    assert best_match["text"] == text_c1
    # Since the embedding is deterministic, similarity score should be exactly 1.0 (or very close)
    assert math.isclose(best_match["score"], 1.0, abs_tol=1e-4)

    # Test deletion
    delete_success = VectorDB.delete_document(doc_id)
    assert delete_success is True

    # Verify document and chunks are deleted
    assert VectorDB.get_document(doc_id) is None
    assert len(VectorDB.get_document_chunks(doc_id)) == 0
