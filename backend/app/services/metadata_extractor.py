import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import fitz  # PyMuPDF
import httpx
from pydantic import BaseModel, Field

from app.services.openrouter import OpenRouterService

logger = logging.getLogger("metadata-extractor")

# Expresión regular para detectar patrones de DOI (Digital Object Identifier)
# Ej: 10.1000/xyz123
DOI_PATTERN = re.compile(r'\b(10\.\d{4,9}/[^\s,;"\'<>]+)', re.IGNORECASE)

# Expresión regular para detectar IDs de arXiv
# Formato moderno: arXiv:YYMM.NNNN o arXiv:YYMM.NNNNNvN
# Formato antiguo: arXiv:arch-ive/YYMMNNN
ARXIV_PATTERN = re.compile(
    r'arxiv:\s*([a-z\-]+(?:\.[a-z\-]+)?/\d{7}(v\d+)?|\d{4}\.\d{4,5}(v\d+)?)\b',
    re.IGNORECASE
)


class PaperMetadata(BaseModel):
    """Modelo estructurado que representa los metadatos de un paper científico."""

    title: str | None = Field(default=None, description="Título del paper")
    authors: list[str] = Field(default_factory=list, description="Lista de autores del paper")
    journal: str | None = Field(default=None, description="Nombre de la revista, conferencia o diario")
    year: int | None = Field(default=None, description="Año de publicación")
    doi: str | None = Field(default=None, description="Identificador DOI del paper")
    abstract: str | None = Field(default=None, description="Resumen o abstract del paper")
    extraction_source: str = Field(
        description="Origen de la extracción de metadatos (embedded, doi, llm, fallback)"
    )


def is_valid_title(title: str | None) -> bool:
    """Verifica si un título embebido en el PDF parece ser un título real e informativo."""
    if not title:
        return False
    title_clean = title.strip()
    title_lower = title_clean.lower()
    
    # Descartar títulos vacíos o demasiado cortos
    if len(title_clean) < 6:
        return False
        
    # Descartar títulos típicos autogenerados, temporales o nombres de archivo
    invalid_keywords = [
        "untitled", "documento sin título", "microsoft word", "latex", 
        "pdf", "tmp", "temp", "draft", "placeholder", "untitled document",
        "sin título", "untitled.pdf"
    ]
    if any(k in title_lower for k in invalid_keywords):
        return False
        
    # Descartar si parece un nombre de archivo directo
    if title_lower.endswith(".pdf"):
        return False
        
    return True


def find_doi_in_text(text: str) -> str | None:
    """Busca patrones de DOI en un texto y realiza una limpieza básica de caracteres de puntuación."""
    match = DOI_PATTERN.search(text)
    if match:
        doi = match.group(1)
        # Limpiar puntuación común que se pueda haber colado al final del DOI
        doi = doi.rstrip(".-,;)")
        return doi
    return None


def find_arxiv_id_in_text(text: str) -> str | None:
    """Busca patrones de arXiv ID en el texto."""
    match = ARXIV_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


async def fetch_arxiv_metadata(arxiv_id: str) -> dict | None:
    """Consulta la API pública de arXiv para recuperar los metadatos Atom (XML)."""
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                return parse_arxiv_xml(response.text)
            else:
                logger.warning(f"La API de arXiv retornó código {response.status_code} para el ID: {arxiv_id}")
        except Exception as e:
            logger.error(f"Error consultando la API de arXiv para el ID {arxiv_id}: {e}")
    return None


def parse_arxiv_xml(xml_content: str) -> dict | None:
    """Parsea la respuesta Atom (XML) de arXiv y la extrae en un diccionario."""
    try:
        namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(xml_content)
        entry = root.find('atom:entry', namespaces)
        if entry is None:
            return None
            
        id_element = entry.find('atom:id', namespaces)
        if id_element is None or not id_element.text:
            return None
            
        title_element = entry.find('atom:title', namespaces)
        title = title_element.text.strip().replace('\n', ' ') if title_element is not None else None
        if not title:
            return None
            
        summary_element = entry.find('atom:summary', namespaces)
        abstract = summary_element.text.strip().replace('\n', ' ') if summary_element is not None else None
        
        authors = []
        for author in entry.findall('atom:author', namespaces):
            name_el = author.find('atom:name', namespaces)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())
                
        published_element = entry.find('atom:published', namespaces)
        year = None
        if published_element is not None and published_element.text:
            try:
                year = int(published_element.text.split('-')[0])
            except ValueError:
                pass
                
        doi_element = entry.find('atom:doi', namespaces)
        doi = doi_element.text.strip() if doi_element is not None else None
        
        return {
            "title": title,
            "authors": authors,
            "journal": "arXiv",
            "year": year,
            "doi": doi,
            "abstract": abstract
        }
    except Exception as e:
        logger.error(f"Error parseando XML de arXiv: {e}")
    return None


async def fetch_crossref_metadata(doi: str) -> dict | None:
    """Consulta la API pública de Crossref para recuperar los metadatos de un DOI."""
    url = f"https://api.crossref.org/works/{doi}"
    headers = {
        "User-Agent": "lectura-pdf-metadata-extractor/1.0 (mailto:mrepetto@example.com)"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"La API de Crossref retornó código {response.status_code} para el DOI: {doi}")
        except Exception as e:
            logger.error(f"Error consultando la API de Crossref para el DOI {doi}: {e}")
    return None


def parse_crossref_response(data: dict) -> dict:
    """Transforma la estructura de respuesta de Crossref al formato simplificado de metadatos."""
    work = data.get("message", {})
    
    # El título en Crossref suele ser una lista de strings
    title_list = work.get("title", [])
    title = title_list[0] if title_list else None
    
    # Extraer nombres de autores
    authors = []
    for author_data in work.get("author", []):
        given = author_data.get("given", "").strip()
        family = author_data.get("family", "").strip()
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)
            
    # Revista o contenedor de publicación
    container_list = work.get("container-title", [])
    journal = container_list[0] if container_list else None
    
    # Extraer el año de publicación (evaluando de más preciso a menos preciso)
    year = None
    for date_type in ["published-print", "published-online", "issued", "created"]:
        date_parts = work.get(date_type, {}).get("date-parts", [])
        if date_parts and date_parts[0] and date_parts[0][0] is not None:
            try:
                year = int(date_parts[0][0])
                break
            except ValueError:
                continue
                
    return {
        "title": title,
        "authors": authors,
        "journal": journal,
        "year": year,
        "doi": work.get("DOI"),
        "abstract": work.get("abstract")
    }


async def extract_metadata_via_llm(text_sample: str) -> dict | None:
    """Usa la LLM configurada a través de OpenRouter para extraer los metadatos estructurados del paper."""
    prompt = (
        "Eres un extractor de metadatos académicos de alta precisión.\n"
        "A partir del siguiente fragmento de texto extraído de las primeras páginas de un paper científico, "
        "identifica los siguientes campos y devuélvelos estrictamente en formato JSON válido:\n"
        "{\n"
        "  \"title\": \"Título del paper\",\n"
        "  \"authors\": [\"Autor 1\", \"Autor 2\"],\n"
        "  \"journal\": \"Nombre de la revista, conferencia o diario donde se publicó\",\n"
        "  \"year\": 2023,\n"
        "  \"doi\": \"DOI si está presente (ej. 10.1000/xyz123)\",\n"
        "  \"abstract\": \"Resumen/Abstract del paper\"\n"
        "}\n\n"
        "Reglas:\n"
        "1. Si no encuentras alguno de los campos, devuélvelo como null.\n"
        "2. No agregues explicaciones, preámbulos ni bloques de texto adicionales fuera del JSON.\n"
        "3. El campo 'authors' debe ser una lista de strings.\n"
        "4. El campo 'year' debe ser un número entero o null.\n\n"
        "Texto del paper:\n"
        f"\"\"\"\n{text_sample}\n\"\"\""
    )
    
    messages = [
        {"role": "system", "content": "Eres un asistente experto en análisis y estructuración de papers científicos. Respondes únicamente con un objeto JSON válido."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response_text = await OpenRouterService.get_chat_completion(messages)
        
        # Extraer el JSON de manera robusta buscando el primer '{' y el último '}'
        cleaned_response = response_text.strip()
        start = cleaned_response.find('{')
        end = cleaned_response.rfind('}')
        if start != -1 and end != -1 and end > start:
            cleaned_response = cleaned_response[start:end+1]
            
        metadata_dict = json.loads(cleaned_response)
        return metadata_dict
    except Exception as e:
        logger.error(f"Error procesando la respuesta del LLM para extracción de metadatos: {e}")
        return None


async def extract_paper_metadata(file_bytes: bytes, filename: str = "document.pdf") -> PaperMetadata:
    """Extrae metadatos de un paper científico en cascada:
    
    1. Metadatos embebidos en el PDF (PyMuPDF)
    2. Identificación de arXiv ID y consulta a la API de arXiv
    3. Identificación del DOI y consulta a la API de Crossref
    4. Análisis del texto de la primera página mediante LLM (OpenRouter)
    5. Fallback básico si todo falla.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    # ----------------------------------------------------
    # Paso 1: Metadatos embebidos en el archivo PDF
    # ----------------------------------------------------
    try:
        embedded = doc.metadata
        title = embedded.get("title")
        if is_valid_title(title):
            logger.info("Metadatos embebidos extraídos con éxito del PDF.")
            authors_raw = embedded.get("author", "")
            authors = []
            if authors_raw:
                # Separar autores por comas, punto y coma o la palabra 'and'
                split_authors = re.split(r'[,;]|\band\b', authors_raw)
                authors = [a.strip() for a in split_authors if a.strip()]
                
            # Extraer año de la fecha de creación del PDF como fallback
            year = None
            creation_date = embedded.get("creationDate", "")
            if creation_date and len(creation_date) >= 6 and creation_date.startswith("D:"):
                try:
                    year = int(creation_date[2:6])
                except ValueError:
                    pass
                    
            doc.close()
            return PaperMetadata(
                title=title.strip(),
                authors=authors,
                journal=embedded.get("subject") or None,
                year=year,
                doi=None,
                abstract=None,
                extraction_source="embedded"
            )
    except Exception as e:
        logger.warning(f"Error extrayendo metadatos embebidos: {e}")
        
    # ----------------------------------------------------
    # Paso 2: Búsqueda de arXiv ID en el texto y consulta a arXiv API
    # ----------------------------------------------------
    try:
        # Escanear las dos primeras páginas buscando un arXiv ID
        num_pages_to_scan = min(2, len(doc))
        arxiv_id = None
        for i in range(num_pages_to_scan):
            page_text = doc[i].get_text("text")
            arxiv_id = find_arxiv_id_in_text(page_text)
            if arxiv_id:
                break
                
        if arxiv_id:
            logger.info(f"arXiv ID detectado en el documento: '{arxiv_id}'. Consultando arXiv API...")
            arxiv_data = await fetch_arxiv_metadata(arxiv_id)
            if arxiv_data and arxiv_data.get("title"):
                logger.info("Metadatos extraídos con éxito a través de arXiv por ID.")
                doc.close()
                return PaperMetadata(
                    title=arxiv_data["title"].strip(),
                    authors=arxiv_data["authors"],
                    journal=arxiv_data["journal"],
                    year=arxiv_data["year"],
                    doi=arxiv_data["doi"],
                    abstract=arxiv_data["abstract"],
                    extraction_source="arxiv"
                )
    except Exception as e:
        logger.warning(f"Error extrayendo metadatos por arXiv ID: {e}")

    # ----------------------------------------------------
    # Paso 3: Búsqueda de DOI en el texto y consulta a Crossref
    # ----------------------------------------------------
    try:
        # Escanear las dos primeras páginas buscando un DOI
        num_pages_to_scan = min(2, len(doc))
        doi = None
        for i in range(num_pages_to_scan):
            page_text = doc[i].get_text("text")
            doi = find_doi_in_text(page_text)
            if doi:
                break
                
        if doi:
            logger.info(f"DOI detectado en el documento: '{doi}'. Consultando Crossref...")
            crossref_data = await fetch_crossref_metadata(doi)
            if crossref_data:
                parsed_data = parse_crossref_response(crossref_data)
                if parsed_data.get("title"):
                    logger.info("Metadatos extraídos con éxito a través de Crossref por DOI.")
                    doc.close()
                    return PaperMetadata(
                        title=parsed_data["title"].strip(),
                        authors=parsed_data["authors"],
                        journal=parsed_data["journal"],
                        year=parsed_data["year"],
                        doi=parsed_data["doi"],
                        abstract=parsed_data["abstract"],
                        extraction_source="doi"
                    )
    except Exception as e:
        logger.warning(f"Error extrayendo metadatos por DOI: {e}")
        
    # ----------------------------------------------------
    # Paso 4: Extracción mediante LLM (OpenRouter)
    # ----------------------------------------------------
    try:
        logger.info("Metadatos embebidos, arXiv y DOI fallidos. Pasando a extracción mediante LLM...")
        
        # Unificar el texto de las primeras páginas para contexto del LLM
        first_pages_text = ""
        pages_to_llm = min(2, len(doc))
        for i in range(pages_to_llm):
            first_pages_text += doc[i].get_text("text") + "\n"
            
        # Limitar longitud para evitar sobrecargar tokens
        first_pages_text = first_pages_text[:5000]
        
        llm_data = await extract_metadata_via_llm(first_pages_text)
        if llm_data and llm_data.get("title"):
            logger.info("Metadatos extraídos con éxito a través del LLM.")
            doc.close()
            
            # Sanitizar tipo de autores y año
            authors = llm_data.get("authors", [])
            if isinstance(authors, str):
                authors = [authors]
            elif not isinstance(authors, list):
                authors = []
                
            year = llm_data.get("year")
            if year is not None:
                try:
                    year = int(year)
                except ValueError:
                    year = None
                    
            return PaperMetadata(
                title=llm_data.get("title").strip(),
                authors=authors,
                journal=llm_data.get("journal"),
                year=year,
                doi=llm_data.get("doi"),
                abstract=llm_data.get("abstract"),
                extraction_source="llm"
            )
    except Exception as e:
        logger.warning(f"Error extrayendo metadatos a través de la LLM: {e}")
        
    # ----------------------------------------------------
    # Paso 5: Fallback básico si todo lo anterior falla
    # ----------------------------------------------------
    logger.warning("Todos los mecanismos de extracción fallaron. Generando metadatos mínimos por fallback.")
    doc.close()
    
    # Utilizar el nombre del archivo formateado como título provisional
    fallback_title = filename.replace(".pdf", "").replace("_", " ").replace("-", " ")
    
    return PaperMetadata(
        title=fallback_title.strip(),
        authors=[],
        journal=None,
        year=None,
        doi=None,
        abstract=None,
        extraction_source="fallback"
    )
