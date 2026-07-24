import abc
import hashlib
import math
import random


class BaseEmbeddingService(abc.ABC):
    """Interfaz base para servicios de generación de embeddings."""

    @abc.abstractmethod
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos."""
        pass

    @abc.abstractmethod
    def get_query_embedding(self, query: str) -> list[float]:
        """Genera embedding para una única consulta (query)."""
        pass


class MockEmbeddingService(BaseEmbeddingService):
    """Servicio mock que genera embeddings deterministas de 768 dimensiones.

    Utiliza el hash SHA-256 del texto como semilla para asegurar que el mismo
    texto siempre produzca el mismo vector normalizado a longitud unitaria (L2 norm = 1.0).
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def _generate_vector(self, text: str) -> list[float]:
        """Genera un vector unitario determinista basado en el hash del texto."""
        # Obtener el hash SHA-256 del texto
        hasher = hashlib.sha256(text.encode("utf-8"))
        seed_bytes = hasher.digest()
        # Usar los primeros 8 bytes como un entero de 64 bits para inicializar la semilla
        seed_int = int.from_bytes(seed_bytes[:8], byteorder="big")

        # Guardar el estado actual del generador random global para no afectar otras partes de la app
        state = random.getstate()

        try:
            random.seed(seed_int)
            # Generar números aleatorios entre -1.0 y 1.0
            vector = [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]

            # Normalizar el vector a longitud L2 = 1.0
            norm = math.sqrt(sum(x * x for x in vector))
            if norm > 0:
                vector = [x / norm for x in vector]
            else:
                vector = [0.0] * self.dimension
            return vector
        finally:
            # Restaurar el estado global de random
            random.setstate(state)

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera una lista de embeddings deterministas para una lista de fragmentos."""
        return [self._generate_vector(t) for t in texts]

    def get_query_embedding(self, query: str) -> list[float]:
        """Genera un embedding determinista para una consulta."""
        return self._generate_vector(query)
