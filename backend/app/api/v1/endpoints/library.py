import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.services.embeddings import get_embedding_service
from app.services.openrouter import OpenRouterService
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
async def search_library(
    q: str = Query(..., description="Consulta de búsqueda semántica en lenguaje natural"),
    limit: int = Query(5, ge=1, le=50, description="Cantidad final de fragmentos a retornar (Reranked)"),
    vector_limit: int = Query(
        20, ge=1, le=100, description="Cantidad de fragmentos iniciales de la búsqueda vectorial"
    ),
):
    """Buscar semánticamente fragmentos de texto en la biblioteca usando embeddings y reranking."""
    try:
        if not q.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La consulta de búsqueda no puede estar vacía.",
            )

        # 1. Obtener el embedding usando la fábrica
        embedding_service = get_embedding_service()
        query_vector = await embedding_service.get_query_embedding(q)

        # 2. Realizar la búsqueda vectorial inicial con vector_limit
        results = VectorDB.search_chunks(query_vector, limit=vector_limit)

        if not results:
            return []

        # 3. Aplicar Reranking si se usa OpenRouter y hay clave de API configurada
        if settings.EMBEDDING_PROVIDER.lower() == "openrouter" and settings.OPENROUTER_API_KEY:
            try:
                texts = [res["text"] for res in results]
                reranked_results = await OpenRouterService.rerank(query=q, documents=texts, top_n=limit)

                final_results = []
                for item in reranked_results:
                    idx = item["index"]
                    if 0 <= idx < len(results):
                        chunk_data = results[idx].copy()
                        chunk_data["score"] = float(item["relevance_score"])
                        final_results.append(chunk_data)
                return final_results
            except Exception as e:
                logger.error(f"Error durante Reranking: {e}. Aplicando fallback a búsqueda vectorial pura.")
                return results[:limit]
        else:
            # Fallback en modo mock o sin API key: retornar los primeros 'limit' resultados
            return results[:limit]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando búsqueda semántica para '{q}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la búsqueda semántica.",
        ) from e
