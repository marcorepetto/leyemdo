import abc
import asyncio
import hashlib
import math
import random
from typing import List

from app.core.config import settings
from app.services.openrouter import OpenRouterService


class BaseEmbeddingService(abc.ABC):
    """Interfaz base para servicios de generación de embeddings."""

    @abc.abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos (asíncrono)."""
        pass

    @abc.abstractmethod
    async def get_query_embedding(self, query: str) -> List[float]:
        """Genera embedding para una única consulta (asíncrono)."""
        pass


class MockEmbeddingService(BaseEmbeddingService):
    """Servicio mock que genera embeddings deterministas.

    Utiliza el hash SHA-256 del texto como semilla para asegurar que el mismo
    texto siempre produzca el mismo vector normalizado a longitud unitaria (L2 norm = 1.0).
    """

    def __init__(self, dimension: int = 2048):
        self.dimension = dimension

    def _generate_vector(self, text: str) -> List[float]:
        """Genera un vector unitario determinista basado en el hash del texto."""
        hasher = hashlib.sha256(text.encode("utf-8"))
        seed_bytes = hasher.digest()
        seed_int = int.from_bytes(seed_bytes[:8], byteorder="big")

        state = random.getstate()
        try:
            random.seed(seed_int)
            vector = [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]
            norm = math.sqrt(sum(x * x for x in vector))
            if norm > 0:
                vector = [x / norm for x in vector]
            else:
                vector = [0.0] * self.dimension
            return vector
        finally:
            random.setstate(state)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Genera una lista de embeddings deterministas de forma asíncrona."""
        # Simular asincronía básica
        await asyncio.sleep(0.0)
        return [self._generate_vector(t) for t in texts]

    async def get_query_embedding(self, query: str) -> List[float]:
        """Genera un embedding determinista para una consulta de forma asíncrona."""
        await asyncio.sleep(0.0)
        return self._generate_vector(query)


class OpenRouterEmbeddingService(BaseEmbeddingService):
    """Servicio que consume la API de OpenRouter para generar embeddings reales."""

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Llama asíncronamente al servicio OpenRouter para embeddings por lote."""
        return await OpenRouterService.get_embeddings(texts)

    async def get_query_embedding(self, query: str) -> List[float]:
        """Llama asíncronamente al servicio OpenRouter para un embedding de query."""
        results = await OpenRouterService.get_embeddings([query])
        return results[0]


def get_embedding_service() -> BaseEmbeddingService:
    """Fábrica que retorna el servicio de embeddings configurado."""
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "openrouter":
        return OpenRouterEmbeddingService()
    elif provider == "mock":
        return MockEmbeddingService(dimension=settings.EMBEDDING_DIMENSION)
    else:
        # Fallback a mock en caso de valor desconocido
        return MockEmbeddingService(dimension=settings.EMBEDDING_DIMENSION)
