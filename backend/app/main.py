import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.vector_db import VectorDB

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("backend-base")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION}...")
    logger.info(f"Rutas de API disponibles bajo el prefijo {settings.API_V1_STR}")
    try:
        VectorDB.init_db()
        logger.info("Base de datos vectorial inicializada correctamente.")
    except Exception as e:
        logger.error(f"Error inicializando la base de datos vectorial: {e}", exc_info=True)
    yield
    logger.info(f"Apagando {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Enable CORS for local cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)
