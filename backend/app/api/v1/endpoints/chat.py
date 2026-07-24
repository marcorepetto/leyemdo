import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.services.embeddings import get_embedding_service
from app.services.openrouter import OpenRouterService
from app.services.prompt_templates import compile_tutor_prompt
from app.services.vector_db import ChatMessageModel, VectorDB

router = APIRouter()
logger = logging.getLogger("chat-endpoints")


class ChatMessageRequest(BaseModel):
    document_id: str
    message: str


@router.post("/message")
async def send_chat_message(request: ChatMessageRequest):
    """Envia una pregunta del usuario, ejecuta RAG y responde mediante Server-Sent Events (SSE)."""
    document_id = request.document_id
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje no puede estar vacío.",
        )

    # 1. Verificar existencia del documento
    doc = VectorDB.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} no encontrado en la biblioteca.",
        )

    try:
        # 2. Generar el embedding real de la consulta del usuario
        embedding_service = get_embedding_service()
        query_vector = await embedding_service.get_query_embedding(message)

        # 3. Recuperar Top K (5) chunks de LanceDB
        chunks = VectorDB.search_chunks(query_vector, limit=5)
        # Filtrar solo chunks que pertenezcan a este documento
        doc_chunks = [c for c in chunks if c["document_id"] == document_id]

        # 4. Obtener el historial conversacional
        history = VectorDB.get_chat_history(document_id)

        # 5. Compilar prompt de sistema (Tutor ZDP + Contexto)
        system_prompt = compile_tutor_prompt(doc_chunks)

        # 6. Estructurar mensajes para OpenRouter
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Agregar la nueva pregunta del usuario
        messages.append({"role": "user", "content": message})

        # 7. Crear generador asíncrono para Server-Sent Events
        async def event_generator():
            collected_response = []
            try:
                # Transmitir los tokens de OpenRouter
                async for chunk in OpenRouterService.get_chat_stream(messages):
                    collected_response.append(chunk)
                    yield {"data": chunk}
            except Exception as e:
                logger.error(f"Error en streaming de chat: {e}", exc_info=True)
                yield {"data": f"\n[Error de comunicación con el Tutor: {e}]"}
            finally:
                # Al finalizar la lectura de streaming por el cliente, persistir en base de datos
                full_text = "".join(collected_response).strip()
                if full_text:
                    # Crear modelos de mensajes
                    user_msg = ChatMessageModel(
                        message_id=str(uuid.uuid4()),
                        document_id=document_id,
                        role="user",
                        content=message,
                        timestamp=datetime.utcnow(),
                    )
                    assistant_msg = ChatMessageModel(
                        message_id=str(uuid.uuid4()),
                        document_id=document_id,
                        role="assistant",
                        content=full_text,
                        timestamp=datetime.utcnow(),
                    )
                    try:
                        VectorDB.add_chat_messages([user_msg, assistant_msg])
                    except Exception as ex:
                        logger.error(f"Error persistiendo mensajes de chat: {ex}", exc_info=True)

        return EventSourceResponse(event_generator())

    except Exception as e:
        logger.error(f"Error al procesar mensaje de chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el mensaje de chat: {e}",
        ) from e


@router.get("/history/{document_id}")
def get_chat_history(document_id: str):
    """Obtiene el historial completo de mensajes asociados a un documento."""
    doc = VectorDB.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} no encontrado.",
        )
    return VectorDB.get_chat_history(document_id)


@router.delete("/history/{document_id}")
def clear_chat_history(document_id: str):
    """Elimina el historial de conversación asociado a un documento."""
    doc = VectorDB.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} no encontrado.",
        )
    VectorDB.clear_chat_history(document_id)
    return {"status": "success", "message": f"Historial del documento {document_id} eliminado exitosamente."}
