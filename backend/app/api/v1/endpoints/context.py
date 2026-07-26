import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.embeddings import get_embedding_service
from app.services.openrouter import OpenRouterService
from app.services.prompt_templates import SYSTEM_PROMPT_TRANSLATE, compile_explain_prompt
from app.services.vector_db import VectorDB

router = APIRouter()
logger = logging.getLogger("context-endpoints")


class ContextActionRequest(BaseModel):
    document_id: str = Field(..., description="ID del documento activo")
    selected_text: str = Field(..., description="Texto seleccionado por el usuario en el visor")
    target_language: str | None = Field("es", description="Idioma destino (solo para traducción)")
    limit: int = Field(3, ge=1, le=10, description="Límite de resultados a retornar")


@router.post("/explain")
async def explain_context(request: ContextActionRequest):
    """Genera una explicación concisa y didáctica para el texto seleccionado en un documento."""
    document_id = request.document_id
    selected_text = request.selected_text.strip()

    if not selected_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El texto seleccionado no puede estar vacío.",
        )

    # 1. Verificar existencia del documento
    doc = VectorDB.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} no encontrado en la biblioteca.",
        )

    try:
        # 2. Obtener chunks del mismo documento para tener contexto sobre la selección
        embedding_service = get_embedding_service()
        query_vector = await embedding_service.get_query_embedding(selected_text)

        # Buscar hasta 3 chunks del mismo documento para alimentar el contexto de la explicación
        context_chunks = VectorDB.search_chunks(query_vector, limit=3, where=f"document_id = '{document_id}'")

        # 3. Compilar prompt de explicación directa
        system_prompt = compile_explain_prompt(context_chunks)

        # 4. Enviar a OpenRouter (llamada no-streaming)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Por favor, explica el siguiente fragmento seleccionado en el texto:\n\n{selected_text}",
            },
        ]
        explanation = await OpenRouterService.get_chat_completion(messages)

        return {"explanation": explanation}

    except Exception as e:
        logger.error(f"Error en endpoint /explain: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la explicación: {e}",
        ) from e


@router.post("/translate")
async def translate_context(request: ContextActionRequest):
    """Traduce el fragmento de texto seleccionado manteniendo el contexto científico/técnico."""
    selected_text = request.selected_text.strip()
    target_language = request.target_language or "es"

    if not selected_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El texto seleccionado no puede estar vacío.",
        )

    # Verificar existencia del documento
    doc = VectorDB.get_document(request.document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {request.document_id} no encontrado en la biblioteca.",
        )

    try:
        # Formatear el prompt de traducción con el idioma solicitado
        system_prompt = SYSTEM_PROMPT_TRANSLATE.format(target_language=target_language)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": selected_text},
        ]
        translation = await OpenRouterService.get_chat_completion(messages)

        return {"translation": translation}

    except Exception as e:
        logger.error(f"Error en endpoint /translate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la traducción: {e}",
        ) from e


@router.post("/search-related")
async def search_related_context(request: ContextActionRequest):
    """Busca fragmentos semánticamente similares al texto seleccionado en otros documentos de la biblioteca."""
    selected_text = request.selected_text.strip()

    if not selected_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El texto seleccionado no puede estar vacío.",
        )

    # Verificar existencia del documento
    doc = VectorDB.get_document(request.document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {request.document_id} no encontrado en la biblioteca.",
        )

    try:
        # 1. Obtener embedding de la selección
        embedding_service = get_embedding_service()
        query_vector = await embedding_service.get_query_embedding(selected_text)

        # 2. Buscar en LanceDB excluyendo el documento activo
        # Buscamos con un límite algo mayor para asegurar suficientes candidatos
        vector_limit = max(20, request.limit * 3)
        results = VectorDB.search_chunks(
            query_vector, limit=vector_limit, where=f"document_id != '{request.document_id}'"
        )

        if not results:
            return []

        # 3. Aplicar Reranking si se usa OpenRouter y está configurada la clave
        if settings.EMBEDDING_PROVIDER.lower() == "openrouter" and settings.OPENROUTER_API_KEY:
            try:
                texts = [res["text"] for res in results]
                reranked_results = await OpenRouterService.rerank(
                    query=selected_text, documents=texts, top_n=request.limit
                )

                final_results = []
                for item in reranked_results:
                    idx = item["index"]
                    if 0 <= idx < len(results):
                        chunk_data = results[idx].copy()
                        chunk_data["score"] = float(item["relevance_score"])
                        final_results.append(chunk_data)
                return final_results
            except Exception as e:
                logger.error(f"Error en reranking de relacionados: {e}. Usando similitud vectorial pura.")
                return results[: request.limit]
        else:
            return results[: request.limit]

    except Exception as e:
        logger.error(f"Error en endpoint /search-related: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar fragmentos relacionados: {e}",
        ) from e


@router.post("/support")
async def support_context(request: ContextActionRequest):
    """Busca fragmentos semánticamente similares al texto seleccionado dentro del mismo documento."""
    selected_text = request.selected_text.strip()

    if not selected_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El texto seleccionado no puede estar vacío.",
        )

    # Verificar existencia del documento
    doc = VectorDB.get_document(request.document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {request.document_id} no encontrado en la biblioteca.",
        )

    try:
        # 1. Obtener embedding de la selección
        embedding_service = get_embedding_service()
        query_vector = await embedding_service.get_query_embedding(selected_text)

        # 2. Buscar en LanceDB filtrando estrictamente por el documento activo
        results = VectorDB.search_chunks(
            query_vector, limit=request.limit, where=f"document_id = '{request.document_id}'"
        )

        return results

    except Exception as e:
        logger.error(f"Error en endpoint /support: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar soporte interno: {e}",
        ) from e
