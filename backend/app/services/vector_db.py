import logging
import os
from datetime import datetime

import lancedb
from lancedb.pydantic import LanceModel, Vector
from pydantic import Field

from app.core.config import settings

logger = logging.getLogger("vector-db-service")


class DocumentModel(LanceModel):
    """Esquema de la tabla 'documents' en LanceDB."""

    document_id: str = Field(description="Hash SHA-256 único del PDF")
    filename: str = Field(description="Nombre del archivo original")
    pages_count: int = Field(description="Número de páginas del PDF")
    total_chars: int = Field(description="Cantidad de caracteres totales")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)
    reading_progress: float = Field(default=0.0)


class ChunkModel(LanceModel):
    """Esquema de la tabla 'chunks' en LanceDB."""

    chunk_id: str = Field(description="ID único del chunk (document_id + _index)")
    document_id: str = Field(description="Relación lógica con el documento")
    text: str = Field(description="Texto del fragmento")
    page_number: int = Field(description="Página de inicio (1-indexed)")
    pages: list[int] = Field(default_factory=list, description="Lista de páginas que abarca")
    char_start: int = Field(description="Offset de caracter inicial")
    char_end: int = Field(description="Offset de caracter final")
    section: str | None = Field(default=None, description="Sección o título del documento")
    vector: Vector(2048) = Field(description="Embedding del fragmento (2048 dimensiones para Nemotron-3)")


class ChatMessageModel(LanceModel):
    """Esquema de la tabla 'chat_messages' en LanceDB."""

    message_id: str = Field(description="UUID único del mensaje")
    document_id: str = Field(description="Relación lógica con el documento")
    role: str = Field(description="Rol del emisor ('user' o 'assistant')")
    content: str = Field(description="Contenido textual del mensaje")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reasoning_details: str | None = Field(default=None, description="Razonamiento opcional del modelo")


class VectorDB:
    """Manejador y cliente para interactuar con LanceDB sin dependencias de pandas."""

    _db = None

    @classmethod
    def get_db(cls) -> lancedb.DBConnection:
        """Obtiene y cachea la conexión a LanceDB."""
        if cls._db is None:
            db_path = settings.VECTOR_DB_PATH
            # Si es ruta relativa, resolverla a absoluta respecto al directorio del proyecto
            if not os.path.isabs(db_path):
                # Determinar la raíz del proyecto (donde está backend/)
                backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                db_path = os.path.join(backend_root, db_path)

            logger.info(f"Conectando a LanceDB en la ruta: {db_path}")
            os.makedirs(db_path, exist_ok=True)
            cls._db = lancedb.connect(db_path)
        return cls._db

    @classmethod
    def init_db(cls):
        """Inicializa la base de datos creando las tablas si no existen."""
        db = cls.get_db()
        logger.info("Inicializando tablas en LanceDB...")
        db.create_table("documents", schema=DocumentModel, exist_ok=True)
        db.create_table("chunks", schema=ChunkModel, exist_ok=True)
        db.create_table("chat_messages", schema=ChatMessageModel, exist_ok=True)

    @classmethod
    def add_document(cls, doc: DocumentModel, chunks: list[ChunkModel]):
        """Agrega un documento y sus chunks correspondientes a LanceDB."""
        db = cls.get_db()

        doc_table = db.open_table("documents")
        chunk_table = db.open_table("chunks")

        # Insertar documento (debe ser una lista o iterable)
        logger.info(f"Persistiendo documento {doc.document_id} en la base de datos...")
        doc_table.add([doc])

        # Insertar chunks
        if chunks:
            logger.info(f"Persistiendo {len(chunks)} chunks para el documento {doc.document_id}...")
            chunk_table.add(chunks)
        else:
            logger.info(f"No hay chunks para persistir para el documento {doc.document_id}.")

    @classmethod
    def _get_table_names(cls, db) -> list[str]:
        """Obtiene una lista de strings con los nombres de las tablas."""
        tables = db.list_tables()
        return tables.tables if hasattr(tables, "tables") else tables

    @classmethod
    def get_documents(cls) -> list[dict]:
        """Obtiene todos los documentos con su conteo de chunks."""
        db = cls.get_db()
        table_names = cls._get_table_names(db)
        if "documents" not in table_names:
            return []

        doc_table = db.open_table("documents")
        # Obtener todos los documentos como lista de diccionarios (usando to_pylist de Arrow)
        docs = doc_table.to_arrow().to_pylist()

        if not docs:
            return []

        # Calcular el conteo de chunks por documento manualmente sin usar pandas
        counts = {}
        if "chunks" in table_names:
            chunk_table = db.open_table("chunks")
            # Usar proyección Arrow para recuperar solo la columna 'document_id' de manera eficiente
            chunks_arrow = chunk_table.to_arrow()
            if chunks_arrow.num_rows > 0:
                doc_ids = chunks_arrow.column("document_id").to_pylist()
                for doc_id in doc_ids:
                    counts[doc_id] = counts.get(doc_id, 0) + 1

        for doc in docs:
            doc["chunks_count"] = counts.get(doc["document_id"], 0)

            # Normalizar fecha
            if isinstance(doc["added_at"], str):
                try:
                    # Algunos formatos de timestamp de Arrow pueden ser strings
                    doc["added_at"] = datetime.fromisoformat(doc["added_at"])
                except ValueError:
                    pass
            elif isinstance(doc["added_at"], (int, float)):
                doc["added_at"] = datetime.fromtimestamp(doc["added_at"])

        return docs

    @classmethod
    def get_document(cls, document_id: str) -> dict | None:
        """Obtiene un documento específico por su ID."""
        docs = cls.get_documents()
        for doc in docs:
            if doc["document_id"] == document_id:
                return doc
        return None

    @classmethod
    def get_document_chunks(cls, document_id: str) -> list[dict]:
        """Obtiene todos los chunks asociados a un documento."""
        db = cls.get_db()
        table_names = cls._get_table_names(db)
        if "chunks" not in table_names:
            return []

        chunk_table = db.open_table("chunks")
        # Filtrar usando búsqueda en LanceDB
        chunks = chunk_table.search().where(f"document_id = '{document_id}'").to_list()

        # Eliminar el campo '_distance' si se incluye automáticamente en to_list
        for chunk in chunks:
            chunk.pop("_distance", None)

        return chunks

    @classmethod
    def delete_document(cls, document_id: str) -> bool:
        """Elimina un documento, sus chunks y su historial de chat de la base de datos."""
        db = cls.get_db()
        table_names = cls._get_table_names(db)

        if "documents" not in table_names or "chunks" not in table_names:
            return False

        doc_table = db.open_table("documents")
        chunk_table = db.open_table("chunks")

        # Verificar existencia
        docs = doc_table.search().where(f"document_id = '{document_id}'").to_list()
        if not docs:
            logger.warning(f"Intento de eliminar documento inexistente: {document_id}")
            return False

        # Eliminar de la tabla documents
        doc_table.delete(f"document_id = '{document_id}'")

        # Eliminar de la tabla chunks
        chunk_table.delete(f"document_id = '{document_id}'")

        # Eliminar de la tabla chat_messages si existe
        if "chat_messages" in table_names:
            chat_table = db.open_table("chat_messages")
            chat_table.delete(f"document_id = '{document_id}'")

        logger.info(f"Documento {document_id}, chunks e historial de chat eliminados correctamente.")
        return True

    @classmethod
    def search_chunks(cls, query_vector: list[float], limit: int = 5, where: str | None = None) -> list[dict]:
        """Realiza una búsqueda semántica de vecinos más cercanos en la tabla de chunks, con filtro where opcional."""
        db = cls.get_db()
        table_names = cls._get_table_names(db)
        if "chunks" not in table_names:
            return []

        chunk_table = db.open_table("chunks")
        # Realiza la búsqueda vectorial en LanceDB
        search_query = chunk_table.search(query_vector)
        if where:
            search_query = search_query.where(where)
        results = search_query.limit(limit).to_list()

        # Formatear resultados
        formatted_results = []
        for res in results:
            distance = res.get("_distance", 0.0)
            score = max(0.0, 1.0 - (distance / 2.0))

            pages = res.get("pages", [])
            if hasattr(pages, "tolist"):
                pages = pages.tolist()

            vector = res.get("vector", [])
            if hasattr(vector, "tolist"):
                vector = vector.tolist()

            formatted_results.append(
                {
                    "chunk_id": res.get("chunk_id"),
                    "document_id": res.get("document_id"),
                    "text": res.get("text"),
                    "page_number": int(res.get("page_number", 1)),
                    "pages": pages,
                    "char_start": int(res.get("char_start", 0)),
                    "char_end": int(res.get("char_end", 0)),
                    "section": res.get("section"),
                    "score": float(score),
                    "distance": float(distance),
                }
            )

        return formatted_results

    @classmethod
    def add_chat_messages(cls, messages: list[ChatMessageModel]):
        """Guarda mensajes de chat en la base de datos."""
        db = cls.get_db()
        table = db.open_table("chat_messages")
        table.add(messages)
        logger.info(f"Guardados {len(messages)} mensajes de chat en LanceDB.")

    @classmethod
    def get_chat_history(cls, document_id: str) -> list[dict]:
        """Recupera el historial de chat de un documento ordenado cronológicamente."""
        db = cls.get_db()
        table_names = cls._get_table_names(db)
        if "chat_messages" not in table_names:
            return []

        table = db.open_table("chat_messages")
        messages = table.search().where(f"document_id = '{document_id}'").to_list()

        # Formatear y ordenar
        for msg in messages:
            msg.pop("_distance", None)

            # Normalizar timestamp
            if isinstance(msg["timestamp"], str):
                try:
                    msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
                except ValueError:
                    pass
            elif isinstance(msg["timestamp"], (int, float)):
                msg["timestamp"] = datetime.fromtimestamp(msg["timestamp"])

        # Ordenar por timestamp cronológicamente
        messages.sort(key=lambda x: x.get("timestamp", datetime.min))

        # Formatear timestamp a ISO-string
        for msg in messages:
            if isinstance(msg["timestamp"], datetime):
                msg["timestamp"] = msg["timestamp"].isoformat()

        return messages

    @classmethod
    def clear_chat_history(cls, document_id: str) -> bool:
        """Limpia el historial de chat de un documento."""
        db = cls.get_db()
        table_names = cls._get_table_names(db)
        if "chat_messages" not in table_names:
            return False

        table = db.open_table("chat_messages")
        table.delete(f"document_id = '{document_id}'")
        logger.info(f"Historial de chat para documento {document_id} eliminado.")
        return True
