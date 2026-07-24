import hashlib
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.services.ingest import IN_MEMORY_DB, TASK_STATUS, run_ingest_pipeline

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    profile: str = Query(
        "paper", description="Perfil de segmentación ('paper' o 'book')"
    ),
    chunk_size: int | None = Query(
        None, description="Tamaño de chunk manual (sobrescribe perfil)"
    ),
    chunk_overlap: int | None = Query(
        None, description="Solapamiento manual (sobrescribe perfil)"
    ),
):
    """Sube un archivo PDF, calcula su hash y procesa su contenido en segundo plano."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se admiten archivos PDF.",
        )

    # Leer el contenido para calcular el hash SHA-256 (document_id)
    file_bytes = await file.read()
    document_id = hashlib.sha256(file_bytes).hexdigest()

    # Verificar si el documento ya se procesó
    if document_id in IN_MEMORY_DB:
        return {
            "task_id": "already-processed",
            "status": "completed",
            "document_id": document_id,
            "message": "Documento ya procesado anteriormente.",
        }

    # Generar un ID único de tarea
    task_id = str(uuid.uuid4())

    # Inicializar el estado de la tarea en memoria
    TASK_STATUS[task_id] = {
        "status": "processing",
        "document_id": document_id,
        "error": None,
    }

    # Disparar tarea en segundo plano
    background_tasks.add_task(
        run_ingest_pipeline,
        task_id,
        document_id,
        file_bytes,
        profile,
        chunk_size,
        chunk_overlap,
    )

    return {
        "task_id": task_id,
        "status": "processing",
        "document_id": document_id,
    }


@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    """Consulta el estado de una tarea de procesamiento de PDF."""
    if task_id == "already-processed":
        return {"status": "completed", "error": None}

    if task_id not in TASK_STATUS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La tarea especificada no existe.",
        )

    return TASK_STATUS[task_id]


@router.get("/chunks/{document_id}")
def get_document_chunks(document_id: str):
    """Recupera la lista de fragmentos y metadatos del documento procesado."""
    if document_id not in IN_MEMORY_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o no ha finalizado su procesamiento.",
        )

    return IN_MEMORY_DB[document_id]
