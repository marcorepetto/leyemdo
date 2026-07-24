import logging
from datetime import datetime

from app.services.embeddings import get_embedding_service
from app.services.pdf_parser import parse_pdf
from app.services.text_splitter import split_document
from app.services.vector_db import ChunkModel, DocumentModel, VectorDB

logger = logging.getLogger("ingest-service")

# Registro en memoria del estado de las tareas de procesamiento
TASK_STATUS = {}


async def run_ingest_pipeline(
    task_id: str,
    document_id: str,
    file_bytes: bytes,
    filename: str = "document.pdf",
    profile: str = "paper",
    custom_chunk_size: int | None = None,
    custom_chunk_overlap: int | None = None,
):
    """Orquestador que corre como BackgroundTask de FastAPI para procesar el PDF,
    extraer texto, segmentarlo, generar embeddings (reales/mock) y guardarlo en LanceDB.
    """
    TASK_STATUS[task_id] = {
        "status": "processing",
        "document_id": document_id,
        "error": None,
    }

    try:
        logger.info(f"Iniciando procesamiento de tarea {task_id} para el documento {document_id}")

        # 1. Parsear el PDF
        pages = parse_pdf(file_bytes)

        # 2. Configurar parámetros de segmentación basados en el perfil
        if profile == "book":
            chunk_size = 1000
            chunk_overlap = 200
        else:  # 'paper' por defecto
            chunk_size = 500
            chunk_overlap = 100

        # Si se especifican parámetros manuales, sobrescribir
        if custom_chunk_size is not None:
            chunk_size = custom_chunk_size
        if custom_chunk_overlap is not None:
            chunk_overlap = custom_chunk_overlap

        logger.info(
            f"Segmentando {len(pages)} páginas con perfil '{profile}' (size={chunk_size}, overlap={chunk_overlap})"
        )

        # 3. Segmentar el documento en chunks
        chunks = split_document(pages, chunk_size, chunk_overlap)

        # 4. Generar embeddings (reales/mock) para los chunks
        logger.info(f"Generando embeddings para {len(chunks)} chunks...")
        embedding_service = get_embedding_service()
        texts_to_embed = [c["text"] for c in chunks]
        vectors = await embedding_service.get_embeddings(texts_to_embed)

        # 5. Estructurar y guardar en LanceDB
        doc_metadata = DocumentModel(
            document_id=document_id,
            filename=filename,
            pages_count=len(pages),
            total_chars=sum(p["text_len"] for p in pages),
            added_at=datetime.utcnow(),
        )

        chunk_models = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{chunk['chunk_index']}"
            chunk_models.append(
                ChunkModel(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=chunk["text"],
                    page_number=chunk["page_number"],
                    pages=chunk["pages"],
                    char_start=chunk["char_start"],
                    char_end=chunk["char_end"],
                    section=chunk["section"],
                    vector=vectors[i],
                )
            )

        logger.info(f"Guardando {len(chunks)} chunks y documento {document_id} en LanceDB...")
        VectorDB.add_document(doc_metadata, chunk_models)

        TASK_STATUS[task_id]["status"] = "completed"
        logger.info(f"Procesamiento finalizado con éxito para la tarea {task_id}. Chunks guardados: {len(chunks)}")

    except Exception as e:
        logger.exception(f"Error procesando la tarea {task_id}: {str(e)}")
        TASK_STATUS[task_id]["status"] = "failed"
        TASK_STATUS[task_id]["error"] = str(e)
