import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import fitz

from app.services.metadata_extractor import (
    extract_paper_metadata,
    is_valid_title,
    find_doi_in_text,
    PaperMetadata
)


def test_is_valid_title():
    assert is_valid_title("The Quantum Mechanics of Superconductors") is True
    assert is_valid_title("Deep Learning for NLP") is True
    
    assert is_valid_title("") is False
    assert is_valid_title("  ") is False
    assert is_valid_title("short") is False
    assert is_valid_title("untitled") is False
    assert is_valid_title("documento sin título") is False
    assert is_valid_title("Microsoft Word - draft.docx") is False
    assert is_valid_title("paper.pdf") is False


def test_find_doi_in_text():
    text_with_doi = "Please cite this article as DOI: 10.1016/j.jcp.2023.112003 or online at..."
    assert find_doi_in_text(text_with_doi) == "10.1016/j.jcp.2023.112003"
    
    text_with_doi_dot = "The DOI is 10.1109/TCC.2021.3061234."
    assert find_doi_in_text(text_with_doi_dot) == "10.1109/TCC.2021.3061234"
    
    text_without_doi = "There is no doi identifier in this text. Just some characters."
    assert find_doi_in_text(text_without_doi) is None


@pytest.mark.anyio
@patch("app.services.metadata_extractor.fitz.open")
async def test_extract_paper_metadata_embedded(mock_fitz_open):
    # Simular un documento PDF con metadatos embebidos válidos
    mock_doc = MagicMock()
    mock_doc.metadata = {
        "title": "A Great Scientific Paper",
        "author": "John Doe and Jane Smith",
        "subject": "Computer Science Journal",
        "creationDate": "D:20250729215036"
    }
    mock_doc.__len__.return_value = 1
    mock_fitz_open.return_value = mock_doc

    result = await extract_paper_metadata(b"dummy pdf bytes", "test_paper.pdf")
    
    assert isinstance(result, PaperMetadata)
    assert result.title == "A Great Scientific Paper"
    assert result.authors == ["John Doe", "Jane Smith"]
    assert result.journal == "Computer Science Journal"
    assert result.year == 2025
    assert result.doi is None
    assert result.extraction_source == "embedded"
    mock_doc.close.assert_called_once()


@pytest.mark.anyio
@patch("app.services.metadata_extractor.fitz.open")
@patch("app.services.metadata_extractor.fetch_crossref_metadata")
async def test_extract_paper_metadata_doi(mock_fetch_crossref, mock_fitz_open):
    # Simular metadatos embebidos no válidos
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "untitled", "author": ""}
    mock_doc.__len__.return_value = 1
    
    # Simular una página con un DOI en el texto
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This paper has DOI: 10.1016/j.im.2022.1001"
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz_open.return_value = mock_doc

    # Simular respuesta de Crossref
    mock_fetch_crossref.return_value = {
        "message": {
            "title": ["Real Title from Crossref"],
            "author": [
                {"given": "Alice", "family": "Johnson"},
                {"given": "Bob", "family": "Williams"}
            ],
            "container-title": ["Journal of Information Management"],
            "issued": {"date-parts": [[2022, 5, 12]]},
            "DOI": "10.1016/j.im.2022.1001",
            "abstract": "This is the abstract from Crossref API."
        }
    }

    result = await extract_paper_metadata(b"dummy pdf bytes", "test_paper.pdf")
    
    assert isinstance(result, PaperMetadata)
    assert result.title == "Real Title from Crossref"
    assert result.authors == ["Alice Johnson", "Bob Williams"]
    assert result.journal == "Journal of Information Management"
    assert result.year == 2022
    assert result.doi == "10.1016/j.im.2022.1001"
    assert result.abstract == "This is the abstract from Crossref API."
    assert result.extraction_source == "doi"
    mock_fetch_crossref.assert_called_once_with("10.1016/j.im.2022.1001")


@pytest.mark.anyio
@patch("app.services.metadata_extractor.fitz.open")
@patch("app.services.metadata_extractor.fetch_crossref_metadata")
@patch("app.services.metadata_extractor.OpenRouterService.get_chat_completion")
async def test_extract_paper_metadata_llm(mock_get_chat, mock_fetch_crossref, mock_fitz_open):
    # Simular metadatos embebidos no válidos y sin DOI en el texto
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "untitled", "author": ""}
    mock_doc.__len__.return_value = 1
    
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Abstract: We study quantum entanglement..."
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    mock_fetch_crossref.return_value = None

    # Simular respuesta del LLM en formato JSON markdown
    mock_get_chat.return_value = """
    ```json
    {
      "title": "Quantum Entanglement Extracted by LLM",
      "authors": ["Dr. Albert Einstein", "Dr. Nathan Rosen"],
      "journal": "Physical Review",
      "year": 1935,
      "doi": "10.1103/PhysRev.47.777",
      "abstract": "We analyze quantum mechanics foundations..."
    }
    ```
    """

    result = await extract_paper_metadata(b"dummy pdf bytes", "test_paper.pdf")
    
    assert isinstance(result, PaperMetadata)
    assert result.title == "Quantum Entanglement Extracted by LLM"
    assert result.authors == ["Dr. Albert Einstein", "Dr. Nathan Rosen"]
    assert result.journal == "Physical Review"
    assert result.year == 1935
    assert result.doi == "10.1103/PhysRev.47.777"
    assert result.abstract == "We analyze quantum mechanics foundations..."
    assert result.extraction_source == "llm"
    mock_get_chat.assert_called_once()


@pytest.mark.anyio
@patch("app.services.metadata_extractor.fitz.open")
@patch("app.services.metadata_extractor.fetch_crossref_metadata")
@patch("app.services.metadata_extractor.OpenRouterService.get_chat_completion")
async def test_extract_paper_metadata_fallback(mock_get_chat, mock_fetch_crossref, mock_fitz_open):
    # Simular que todo falla (embebidos malos, sin DOI, llamada a LLM que explota o devuelve basura)
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "untitled", "author": ""}
    mock_doc.__len__.return_value = 1
    
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Abstract: Garbage in, garbage out..."
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz_open.return_value = mock_doc
    
    mock_fetch_crossref.return_value = None
    mock_get_chat.side_effect = Exception("LLM connection failed")

    result = await extract_paper_metadata(b"dummy pdf bytes", "deep_learning_survey.pdf")
    
    assert isinstance(result, PaperMetadata)
    assert result.title == "deep learning survey"
    assert result.authors == []
    assert result.journal is None
    assert result.year is None
    assert result.extraction_source == "fallback"


@pytest.mark.anyio
@patch("app.services.metadata_extractor.fitz.open")
@patch("app.services.metadata_extractor.fetch_arxiv_metadata")
async def test_extract_paper_metadata_arxiv(mock_fetch_arxiv, mock_fitz_open):
    # Simular metadatos embebidos no válidos
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "untitled", "author": ""}
    mock_doc.__len__.return_value = 1
    
    # Simular una página con un ID de arXiv en el texto
    mock_page = MagicMock()
    mock_page.get_text.return_value = "arXiv:1706.03762v5 [cs.CL] 12 Jun 2017"
    mock_doc.__getitem__.return_value = mock_page
    mock_fitz_open.return_value = mock_doc

    # Simular respuesta de arXiv
    mock_fetch_arxiv.return_value = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "journal": "arXiv",
        "year": 2017,
        "doi": "10.48550/arxiv.1706.03762",
        "abstract": "We propose a new simple network architecture, the Transformer..."
    }

    result = await extract_paper_metadata(b"dummy pdf bytes", "test_paper.pdf")
    
    assert isinstance(result, PaperMetadata)
    assert result.title == "Attention Is All You Need"
    assert result.authors == ["Ashish Vaswani", "Noam Shazeer"]
    assert result.journal == "arXiv"
    assert result.year == 2017
    assert result.doi == "10.48550/arxiv.1706.03762"
    assert result.abstract == "We propose a new simple network architecture, the Transformer..."
    assert result.extraction_source == "arxiv"
    mock_fetch_arxiv.assert_called_once_with("1706.03762v5")

