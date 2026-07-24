from fastapi import APIRouter

from app.api.v1.endpoints import debug, documents, health, library

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(library.router, prefix="/library", tags=["library"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
