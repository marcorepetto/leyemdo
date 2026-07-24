import json
import logging
from typing import AsyncGenerator

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("openrouter-service")


class OpenRouterService:
    """Cliente para interactuar con la API de OpenRouter (Embeddings y Chat Completions)."""

    @classmethod
    def _get_headers(cls) -> dict:
        """Obtiene las cabeceras estándar para la API de OpenRouter."""
        if not settings.OPENROUTER_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clave de API de OpenRouter (OPENROUTER_API_KEY) no configurada.",
            )
        return {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/mrepetto/lectura",
            "X-OpenRouter-Title": "Lector PDF Inteligente",
        }

    @classmethod
    async def get_embeddings(cls, texts: list[str]) -> list[list[float]]:
        """Genera embeddings reales llamando a la API de OpenRouter."""
        headers = cls._get_headers()
        data = {
            "model": settings.EMBEDDING_MODEL,
            "input": texts,
            "encoding_format": "float",
        }

        url = "https://openrouter.ai/api/v1/embeddings"
        logger.info(
            f"Enviando solicitud de embeddings a OpenRouter ({settings.EMBEDDING_MODEL}) para {len(texts)} textos..."
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
                if response.status_code != 200:
                    logger.error(f"Error de OpenRouter Embeddings API: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OpenRouter Embeddings API error: {response.text}",
                    )

                res_data = response.json()
                embeddings = [item["embedding"] for item in res_data["data"]]
                return embeddings
            except httpx.RequestError as e:
                logger.error(f"Error de red contactando OpenRouter Embeddings: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error de red contactando la API de OpenRouter: {e}",
                ) from e

    @classmethod
    async def get_chat_stream(cls, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Obtiene el flujo de completions en streaming (Server-Sent Events) desde OpenRouter."""
        headers = cls._get_headers()
        data = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "stream": True,
        }

        url = "https://openrouter.ai/api/v1/chat/completions"
        logger.info(f"Iniciando chat stream con OpenRouter ({settings.LLM_MODEL})...")

        # Usar AsyncClient para streaming
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("POST", url, headers=headers, json=data, timeout=60.0) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        error_msg = error_text.decode("utf-8")
                        logger.error(f"Error de OpenRouter Chat API: {response.status_code} - {error_msg}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"OpenRouter Chat API error: {error_msg}",
                        )

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        # OpenRouter devuelve eventos SSE: data: {"choices": [...]}
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            if data_str == "[DONE]":
                                break

                            try:
                                data_json = json.loads(data_str)
                                choices = data_json.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield content
                            except (json.JSONDecodeError, KeyError, IndexError) as e:
                                # Capturar pero no detener el flujo en caso de línea corrupta o latidos SSE vacíos
                                logger.debug(f"Saltada línea SSE no procesable: {e} | Line: {line}")
            except httpx.RequestError as e:
                logger.error(f"Error de red contactando OpenRouter Chat stream: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error de red contactando la API de OpenRouter para Chat completions: {e}",
                ) from e

    @classmethod
    async def rerank(cls, query: str, documents: list[str], top_n: int) -> list[dict]:
        """Llama al endpoint de Reranking de OpenRouter para ordenar documentos por relevancia."""
        if not documents:
            return []

        headers = cls._get_headers()
        formatted_docs = [{"text": doc} for doc in documents]
        data = {
            "model": settings.RERANK_MODEL,
            "query": query,
            "documents": formatted_docs,
            "top_n": top_n,
        }

        url = "https://openrouter.ai/api/v1/rerank"
        logger.info(
            f"Enviando solicitud de Rerank a OpenRouter ({settings.RERANK_MODEL}) "
            f"para {len(documents)} documentos con query '{query[:30]}...' (top_n={top_n})"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
                if response.status_code != 200:
                    logger.error(f"Error de OpenRouter Rerank API: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OpenRouter Rerank API error: {response.text}",
                    )

                res_data = response.json()
                return res_data.get("results", [])
            except httpx.RequestError as e:
                logger.error(f"Error de red contactando OpenRouter Rerank: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error de red contactando la API de OpenRouter Rerank: {e}",
                ) from e
