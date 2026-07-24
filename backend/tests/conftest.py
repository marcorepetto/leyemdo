import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def test_settings_override():
    # Usar un directorio temporal para la base de datos vectorial en los tests
    temp_dir = tempfile.mkdtemp()
    settings.VECTOR_DB_PATH = temp_dir
    # Forzar el proveedor mock para evitar llamadas reales a APIs externas en los tests
    settings.EMBEDDING_PROVIDER = "mock"
    settings.EMBEDDING_DIMENSION = 2048
    settings.LLM_PROVIDER = "mock"  # We will mock chat completions too if needed
    yield
    # Limpiar al finalizar la sesión de pruebas
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="module")
def client():
    from app.main import app
    from app.services.vector_db import VectorDB

    # Reset/reinitialize connection for the new DB path
    VectorDB._db = None
    with TestClient(app) as c:
        yield c
