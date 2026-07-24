import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.services.embeddings import MockEmbeddingService
from app.services.vector_db import VectorDB

router = APIRouter()
logger = logging.getLogger("library-endpoints")


@router.get("/documents")
def list_documents():
    """Listar todos los documentos de la biblioteca con su conteo de chunks."""
    try:
        docs = VectorDB.get_documents()
        return docs
    except Exception as e:
        logger.error(f"Error listando documentos de biblioteca: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al recuperar los documentos de la biblioteca.",
        ) from e


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    """Eliminar un documento y todos sus chunks de la base de datos vectorial."""
    try:
        success = VectorDB.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento con ID {document_id} no encontrado en la biblioteca.",
            )
        return {"status": "success", "message": f"Documento {document_id} eliminado exitosamente."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando documento {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar el documento de la biblioteca.",
        ) from e


@router.get("/search")
def search_library(
    q: str = Query(..., description="Consulta de búsqueda semántica en lenguaje natural"),
    limit: int = Query(5, ge=1, le=50, description="Cantidad máxima de fragmentos a retornar"),
):
    """Buscar semánticamente fragmentos de texto en la biblioteca usando embeddings mock."""
    try:
        if not q.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La consulta de búsqueda no puede estar vacía.",
            )

        # 1. Obtener el embedding mock para la consulta
        embedding_service = MockEmbeddingService()
        query_vector = embedding_service.get_query_embedding(q)

        # 2. Realizar la búsqueda vectorial
        results = VectorDB.search_chunks(query_vector, limit=limit)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando búsqueda semántica para '{q}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la búsqueda semántica.",
        ) from e
