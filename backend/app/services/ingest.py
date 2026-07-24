import logging

from app.services.pdf_parser import parse_pdf
from app.services.text_splitter import split_document

logger = logging.getLogger("ingest-service")

# Base de datos en memoria para almacenamiento temporal de documentos y chunks
IN_MEMORY_DB = {}

# Registro en memoria del estado de las tareas de procesamiento
TASK_STATUS = {}


def run_ingest_pipeline(
    task_id: str,
    document_id: str,
    file_bytes: bytes,
    profile: str = "paper",
    custom_chunk_size: int | None = None,
    custom_chunk_overlap: int | None = None,
):
    """Orquestador que corre como BackgroundTask de FastAPI para procesar el PDF,

    extraer texto, segmentarlo y guardar el resultado.
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

        # 4. Guardar resultados en la base de datos temporal en memoria
        IN_MEMORY_DB[document_id] = {
            "document_id": document_id,
            "chunks": chunks,
            "pages_count": len(pages),
            "total_chars": sum(p["text_len"] for p in pages),
        }

        TASK_STATUS[task_id]["status"] = "completed"
        logger.info(f"Procesamiento finalizado con éxito para la tarea {task_id}. Chunks generados: {len(chunks)}")

    except Exception as e:
        logger.exception(f"Error procesando la tarea {task_id}: {str(e)}")
        TASK_STATUS[task_id]["status"] = "failed"
        TASK_STATUS[task_id]["error"] = str(e)
