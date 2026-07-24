from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.services.openrouter import OpenRouterService


@pytest.mark.anyio
@patch("httpx.AsyncClient.post")
async def test_openrouter_get_embeddings(mock_post):
    # Configure mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "object": "list",
        "data": [
            {"object": "embedding", "index": 0, "embedding": [0.1] * 2048},
            {"object": "embedding", "index": 1, "embedding": [0.2] * 2048},
        ],
    }
    mock_post.return_value = mock_response

    # Force temporary api key
    settings.OPENROUTER_API_KEY = "mock_key"

    texts = ["Hello", "World"]
    embeddings = await OpenRouterService.get_embeddings(texts)

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1] * 2048
    assert embeddings[1] == [0.2] * 2048

    # Verify request headers and payload
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://openrouter.ai/api/v1/embeddings"
    assert kwargs["headers"]["Authorization"] == "Bearer mock_key"
    assert kwargs["json"]["input"] == texts


@pytest.mark.anyio
async def test_openrouter_chat_stream():
    # We will mock client.stream context manager
    mock_response = MagicMock()
    mock_response.status_code = 200

    # Mock iterator lines
    async def mock_aiter_lines():
        yield 'data: {"choices": [{"delta": {"content": "Hello "}}]}'
        yield 'data: {"choices": [{"delta": {"content": "world"}}]}'
        yield "data: [DONE]"

    mock_response.aiter_lines = mock_aiter_lines

    # Mock the AsyncClient.stream method
    mock_client = MagicMock()
    mock_client.stream.return_value.__aenter__.return_value = mock_response

    with patch("httpx.AsyncClient.stream", return_value=mock_client.stream.return_value):
        settings.OPENROUTER_API_KEY = "mock_key"

        messages = [{"role": "user", "content": "Hi"}]
        collected = []
        async for chunk in OpenRouterService.get_chat_stream(messages):
            collected.append(chunk)

        assert "".join(collected) == "Hello world"
