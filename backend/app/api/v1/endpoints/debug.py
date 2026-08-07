# ruff: noqa: E501
import hashlib

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse, Response

from app.services.pdf_debug import draw_debug_annotations
from app.services.pdf_parser import parse_pdf

router = APIRouter()

# Caché temporal en memoria de archivos subidos para depuración
DEBUG_PDF_CACHE = {}


@router.post("/upload")
async def upload_debug_pdf(file: UploadFile = File(...)):
    """Sube un archivo PDF temporalmente en memoria para su visualización y depuración."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se admiten archivos PDF.",
        )

    file_bytes = await file.read()
    document_id = hashlib.sha256(file_bytes).hexdigest()

    # Guardar en caché y calcular total de páginas
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_count = len(doc)
        doc.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo leer el archivo PDF: {str(e)}",
        ) from e

    DEBUG_PDF_CACHE[document_id] = {
        "bytes": file_bytes,
        "pages_count": pages_count,
        "filename": file.filename,
    }

    return {"document_id": document_id, "pages_count": pages_count, "filename": file.filename}


@router.get("/view/{document_id}/page/{page_number}")
def get_debug_page_image(document_id: str, page_number: int):
    """Devuelve la imagen PNG anotada con cajas delimitadoras y orden secuencial."""
    if document_id not in DEBUG_PDF_CACHE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado. Súbelo de nuevo.",
        )

    doc_data = DEBUG_PDF_CACHE[document_id]

    try:
        png_bytes = draw_debug_annotations(doc_data["bytes"], page_number)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    return Response(content=png_bytes, media_type="image/png")


@router.get("/clean-view/{document_id}/page/{page_number}")
def get_clean_page_image(document_id: str, page_number: int):
    """Devuelve la imagen PNG limpia (sin anotaciones en el PDF) para renderizado interactivo en el cliente."""
    if document_id not in DEBUG_PDF_CACHE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado. Súbelo de nuevo.",
        )

    doc_data = DEBUG_PDF_CACHE[document_id]

    try:
        doc = fitz.open(stream=doc_data["bytes"], filetype="pdf")
        if page_number < 1 or page_number > len(doc):
            doc.close()
            raise ValueError(f"Número de página inválido: {page_number}. El documento tiene {len(doc)} páginas.")

        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=150)
        png_bytes = pix.tobytes("png")
        doc.close()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    return Response(content=png_bytes, media_type="image/png")


@router.get("/parsed/{document_id}/page/{page_number}")
def get_parsed_page_data(document_id: str, page_number: int):
    """Devuelve la estructura JSON del parser para una página específica, leyendo directamente desde parse_pdf."""
    if document_id not in DEBUG_PDF_CACHE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado. Súbelo de nuevo.",
        )

    doc_data = DEBUG_PDF_CACHE[document_id]

    try:
        # Cachear el resultado de la función de parsing para evitar procesar repetidamente
        if "parsed_pages" not in doc_data:
            doc_data["parsed_pages"] = parse_pdf(doc_data["bytes"])

        parsed_pages = doc_data["parsed_pages"]

        if page_number < 1 or page_number > len(parsed_pages):
            raise ValueError(f"Número de página inválido: {page_number}. El documento tiene {len(parsed_pages)} páginas.")

        return parsed_pages[page_number - 1]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/ui", response_class=HTMLResponse)
def get_debug_ui():
    """Sirve la interfaz web responsiva y moderna para la visualización interactiva del depurador."""
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Parser Debugger</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        fontFamily: {
                            sans: ['Outfit', 'sans-serif'],
                            mono: ['JetBrains Mono', 'monospace'],
                        }
                    }
                }
            }
        </script>
        <style>
            body {
                background: linear-gradient(135deg, #090d16 0%, #111424 100%);
            }
            .glassmorphism {
                background: rgba(17, 24, 39, 0.7);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            .glass-card {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.04);
            }
            /* Custom Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            ::-webkit-scrollbar-track {
                background: transparent;
            }
            ::-webkit-scrollbar-thumb {
                background: rgba(99, 102, 241, 0.2);
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(99, 102, 241, 0.4);
            }
            
            /* SVG Styles & Animations */
            @keyframes pulse-highlight {
                0% { fill: rgba(99, 102, 241, 0.15); stroke: #6366f1; stroke-width: 2.5; }
                50% { fill: rgba(99, 102, 241, 0.45); stroke: #818cf8; stroke-width: 4.5; }
                100% { fill: rgba(99, 102, 241, 0.15); stroke: #6366f1; stroke-width: 2.5; }
            }
            .pulse-highlight {
                animation: pulse-highlight 1.2s ease-in-out;
            }
        </style>
    </head>
    <body class="min-h-screen max-h-screen text-slate-100 flex flex-col font-sans overflow-hidden">
        <!-- Header -->
        <header class="w-full glassmorphism py-3 px-6 flex justify-between items-center shadow-lg border-b border-indigo-500/10 z-20 shrink-0">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center font-bold text-lg shadow-lg shadow-indigo-500/20">
                    D
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight bg-gradient-to-r from-violet-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">PDF Parser Debugger</h1>
                    <div class="flex items-center gap-2">
                        <p class="text-xs text-indigo-400/80">Estructura & Ordenación de Lectura Directa</p>
                        <span class="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono hidden" id="docTitle"></span>
                    </div>
                </div>
            </div>

            <!-- Page Navigator in Header -->
            <div id="headerPagination" class="flex items-center gap-3 bg-slate-950/40 rounded-xl p-1 px-3 border border-slate-800/80 opacity-40 pointer-events-none transition-all">
                <button id="prevBtn" class="p-1 px-2.5 bg-indigo-600/90 hover:bg-indigo-500 disabled:opacity-20 disabled:pointer-events-none rounded-lg text-xs font-semibold transition-all">
                    ←
                </button>
                <div class="flex items-center gap-1.5 text-xs text-slate-400">
                    <span>Pág.</span>
                    <input type="number" id="pageInput" min="1" value="1" class="w-12 bg-slate-900 border border-slate-700 rounded-md px-1 py-0.5 text-center font-bold text-indigo-300 focus:outline-none focus:border-indigo-500">
                    <span>de <span id="totalPages" class="font-bold text-slate-200">1</span></span>
                </div>
                <button id="nextBtn" class="p-1 px-2.5 bg-indigo-600/90 hover:bg-indigo-500 disabled:opacity-20 disabled:pointer-events-none rounded-lg text-xs font-semibold transition-all">
                    →
                </button>
            </div>

            <div class="text-xs font-semibold px-2.5 py-1 rounded-lg bg-indigo-500/5 border border-indigo-500/20 text-indigo-300/90">
                Direct Parser Output Mode
            </div>
        </header>

        <!-- Main Body -->
        <main class="flex-1 flex flex-col md:flex-row p-4 gap-4 w-full h-[calc(100vh-62px)]">
            
            <!-- Left Sidebar (Controls) -->
            <section class="w-full md:w-72 flex flex-col gap-4 shrink-0 overflow-y-auto pr-1">
                <!-- Upload Box -->
                <div class="glassmorphism rounded-2xl p-4 shadow-xl flex flex-col gap-2.5">
                    <h2 class="font-semibold text-xs uppercase tracking-wider text-indigo-400">Subir PDF</h2>
                    <label for="fileInput" id="dropzone" class="border border-dashed border-indigo-500/20 hover:border-indigo-500/50 rounded-xl p-5 text-center cursor-pointer transition-all duration-300 bg-slate-950/30 hover:bg-slate-950/60 flex flex-col items-center justify-center group">
                        <svg class="w-8 h-8 text-indigo-400/40 group-hover:text-indigo-400/80 transition-colors mb-1.5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
                        </svg>
                        <p class="text-[11px] text-slate-300 font-medium leading-snug">Arrastra tu PDF aquí o haz clic para buscar</p>
                    </label>
                    <input type="file" id="fileInput" accept=".pdf" class="sr-only">
                </div>

                <!-- Debug Options -->
                <div id="optionsCard" class="glassmorphism rounded-2xl p-4 shadow-xl flex flex-col gap-3.5 opacity-40 pointer-events-none transition-all">
                    <h2 class="font-semibold text-xs uppercase tracking-wider text-indigo-400">Capas Visuales</h2>
                    
                    <div class="flex flex-col gap-2.5">
                        <!-- Toggle Blocks -->
                        <label class="flex items-center justify-between cursor-pointer group">
                            <span class="text-xs text-slate-300 group-hover:text-white transition-colors">Mostrar Bloques</span>
                            <div class="relative">
                                <input type="checkbox" id="showBoxesToggle" class="sr-only peer" checked>
                                <div class="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-slate-400 peer-checked:after:bg-indigo-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-950 border border-slate-700/60 peer-checked:border-indigo-500/50"></div>
                            </div>
                        </label>

                        <!-- Toggle Reading Order -->
                        <label class="flex items-center justify-between cursor-pointer group">
                            <span class="text-xs text-slate-300 group-hover:text-white transition-colors">Número de Ordenación</span>
                            <div class="relative">
                                <input type="checkbox" id="showReadingOrderToggle" class="sr-only peer" checked>
                                <div class="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-slate-400 peer-checked:after:bg-indigo-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-950 border border-slate-700/60 peer-checked:border-indigo-500/50"></div>
                            </div>
                        </label>

                        <!-- Toggle Spans -->
                        <label class="flex items-center justify-between cursor-pointer group">
                            <span class="text-xs text-slate-300 group-hover:text-white transition-colors">Mostrar Spans (Tipografía)</span>
                            <div class="relative">
                                <input type="checkbox" id="showSpansToggle" class="sr-only peer">
                                <div class="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-slate-400 peer-checked:after:bg-indigo-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-950 border border-slate-700/60 peer-checked:border-indigo-500/50"></div>
                            </div>
                        </label>

                        <div class="border-t border-slate-800/80 my-1"></div>

                        <!-- Server Side Draw Toggle -->
                        <label class="flex items-center justify-between cursor-pointer group" title="Renderizar anotaciones directo en el PDF del backend">
                            <div class="flex flex-col">
                                <span class="text-xs text-slate-300 group-hover:text-white transition-colors">Anotar en Servidor</span>
                                <span class="text-[9px] text-slate-500">Estático, dibujado por PyMuPDF</span>
                            </div>
                            <div class="relative">
                                <input type="checkbox" id="renderBackendToggle" class="sr-only peer">
                                <div class="w-8 h-4 bg-slate-800 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-slate-400 peer-checked:after:bg-indigo-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-950 border border-slate-700/60 peer-checked:border-indigo-500/50"></div>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- Page Info -->
                <div id="infoCard" class="glassmorphism rounded-2xl p-4 shadow-xl flex flex-col gap-2 opacity-40 pointer-events-none transition-all mt-auto">
                    <h2 class="font-semibold text-xs uppercase tracking-wider text-indigo-400 mb-1">Métricas de la Página</h2>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <div class="bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/50">
                            <div class="text-slate-500 text-[10px]">Caracteres</div>
                            <div class="font-bold text-indigo-300 text-sm mt-0.5" id="charCount">0</div>
                        </div>
                        <div class="bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/50">
                            <div class="text-slate-500 text-[10px]">Bloques Texto</div>
                            <div class="font-bold text-indigo-300 text-sm mt-0.5" id="blocksCount">0</div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Viewer Area (Interactive overlay) -->
            <section class="flex-1 glassmorphism rounded-2xl p-2 shadow-xl flex flex-col min-h-0 relative border border-white/5">
                <!-- Welcome/State Overlay -->
                <div id="noDocState" class="flex flex-col items-center justify-center text-center p-8 transition-opacity duration-300 z-10 m-auto">
                    <div class="w-14 h-14 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 flex items-center justify-center text-indigo-400 shadow-inner mb-4 animate-pulse">
                        <svg class="w-7 h-7" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
                        </svg>
                    </div>
                    <h3 class="text-base font-semibold text-slate-200 mb-1.5">Ningún Documento Cargado</h3>
                    <p class="text-xs text-slate-400 max-w-xs leading-relaxed">Sube un archivo PDF para visualizar e interactuar en tiempo real con las cajas y estructuras del parser.</p>
                </div>

                <!-- Loader -->
                <div id="loadingOverlay" class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center transition-all duration-300 opacity-0 pointer-events-none z-30">
                    <div class="w-10 h-10 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2.5"></div>
                    <p class="text-xs font-medium text-slate-400">Procesando y obteniendo datos de parsing...</p>
                </div>

                <!-- Interactive Viewer Wrapper (Block overflow container) -->
                <div id="viewerWrapper" class="w-full flex-1 min-h-0 p-4 relative overflow-y-auto overflow-x-auto" style="display: none;">
                    <!-- Relative container centered horizontally -->
                    <div class="relative select-none mx-auto" id="viewerContainer" style="width: fit-content;">
                        <!-- PDF Page Image (Clean or Server Annotated) -->
                        <img id="pageImg" class="max-w-full h-auto rounded border border-slate-800 shadow-2xl block" src="" alt="Página del PDF">
                        
                        <!-- SVG interactive layer overlay -->
                        <svg id="svgOverlay" class="absolute top-0 left-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                            <!-- Dynamically generated elements -->
                        </svg>

                        <!-- Dynamic Tooltip -->
                        <div id="debugTooltip" class="absolute pointer-events-none glassmorphism p-3 rounded-xl border border-indigo-500/30 text-left shadow-2xl z-40 max-w-sm w-72 text-xs flex flex-col gap-1 transition-all duration-75" style="display: none;">
                            <!-- Dynamic content -->
                        </div>
                    </div>
                </div>
            </section>

            <!-- Right Sidebar (Metadata and Code Inspector) -->
            <section class="w-full md:w-96 flex flex-col gap-3 shrink-0 glassmorphism rounded-2xl p-4 shadow-xl opacity-40 pointer-events-none transition-all overflow-y-auto" id="inspectorCard">
                <!-- Tabs -->
                <div class="flex border-b border-slate-800/80 mb-2.5 text-center text-xs font-semibold shrink-0">
                    <button id="tabBlocks" class="flex-1 pb-2 border-b-2 border-indigo-500 text-indigo-400 focus:outline-none transition-all">
                        Bloques
                    </button>
                    <button id="tabText" class="flex-1 pb-2 text-slate-400 hover:text-slate-200 border-b-2 border-transparent focus:outline-none transition-all">
                        Texto Plano
                    </button>
                </div>

                <!-- Structured Blocks Tab -->
                <div id="blocksList" class="flex-1 flex flex-col gap-2.5 overflow-y-auto pr-1">
                    <!-- List of block cards -->
                </div>

                <!-- Raw Cleaned Text Tab -->
                <div id="cleanTextContainer" class="flex-1 overflow-auto bg-slate-950/40 p-4 rounded-xl border border-slate-800/50 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap select-text selection:bg-indigo-500/30" style="display: none;">
                    <!-- Plain text output -->
                </div>
            </section>
        </main>

        <script>
            // Elementos DOM
            const dropzone = document.getElementById('dropzone');
            const fileInput = document.getElementById('fileInput');
            
            // Cards a habilitar
            const headerPagination = document.getElementById('headerPagination');
            const optionsCard = document.getElementById('optionsCard');
            const infoCard = document.getElementById('infoCard');
            const inspectorCard = document.getElementById('inspectorCard');
            
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const pageInput = document.getElementById('pageInput');
            const totalPagesSpan = document.getElementById('totalPages');
            
            const noDocState = document.getElementById('noDocState');
            const loadingOverlay = document.getElementById('loadingOverlay');
            const viewerWrapper = document.getElementById('viewerWrapper');
            const viewerContainer = document.getElementById('viewerContainer');
            
            const pageImg = document.getElementById('pageImg');
            const svgOverlay = document.getElementById('svgOverlay');
            const tooltip = document.getElementById('debugTooltip');
            
            const docTitle = document.getElementById('docTitle');
            const charCountSpan = document.getElementById('charCount');
            const blocksCountSpan = document.getElementById('blocksCount');
            const blocksList = document.getElementById('blocksList');
            const cleanTextContainer = document.getElementById('cleanTextContainer');
            
            const tabBlocks = document.getElementById('tabBlocks');
            const tabText = document.getElementById('tabText');

            // Toggles
            const showBoxesToggle = document.getElementById('showBoxesToggle');
            const showReadingOrderToggle = document.getElementById('showReadingOrderToggle');
            const showSpansToggle = document.getElementById('showSpansToggle');
            const renderBackendToggle = document.getElementById('renderBackendToggle');

            // Estado global
            let documentId = '';
            let totalPages = 1;
            let currentPage = 1;
            let pageData = null;
            let filename = '';

            // Inicializar opciones guardadas
            initToggles();

            // Manejo de carga de archivos (gestionado de forma nativa por la etiqueta <label for="fileInput">)
            // Prevenir la navegación predeterminada del navegador al soltar archivos fuera del área
            window.addEventListener('dragover', (e) => e.preventDefault());
            window.addEventListener('drop', (e) => e.preventDefault());

            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.classList.add('border-indigo-500/60', 'bg-slate-950/60');
            });
            dropzone.addEventListener('dragleave', () => {
                dropzone.classList.remove('border-indigo-500/60', 'bg-slate-950/60');
            });
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('border-indigo-500/60', 'bg-slate-950/60');
                if (e.dataTransfer.files.length > 0) {
                    uploadPDF(e.dataTransfer.files[0]);
                }
            });
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    uploadPDF(e.target.files[0]);
                }
            });

            async function uploadPDF(file) {
                if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
                    alert('Por favor selecciona un archivo PDF válido.');
                    return;
                }

                showLoading(true);

                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/api/v1/debug/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) throw new Error('Error subiendo PDF.');

                    const data = await response.json();
                    documentId = data.document_id;
                    totalPages = data.pages_count;
                    filename = data.filename;
                    currentPage = 1;

                    // Habilitar controles visuales
                    [headerPagination, optionsCard, infoCard, inspectorCard].forEach(el => {
                        el.classList.remove('opacity-40', 'pointer-events-none');
                    });
                    
                    docTitle.textContent = filename;
                    docTitle.style.display = 'inline-block';
                    
                    noDocState.style.display = 'none';
                    viewerWrapper.style.display = 'block';

                    updatePaginationUI();
                    await loadPageImage();

                } catch (error) {
                    console.error(error);
                    alert('Error cargando el PDF al servidor.');
                    showLoading(false);
                } finally {
                    fileInput.value = '';
                }
            }

            // Carga la imagen de la página y gatilla el fetching del parser JSON
            async function loadPageImage() {
                if (!documentId) return;
                showLoading(true);

                const useBackendDraw = renderBackendToggle.checked;
                const imgUrl = (useBackendDraw
                    ? `/api/v1/debug/view/${documentId}/page/${currentPage}`
                    : `/api/v1/debug/clean-view/${documentId}/page/${currentPage}`) + `?t=${Date.now()}`;

                pageImg.onload = async () => {
                    pageImg.onload = null;
                    pageImg.onerror = null;

                    if (useBackendDraw) {
                        svgOverlay.style.display = 'none';
                    } else {
                        svgOverlay.style.display = 'block';
                    }

                    // Cargar información de parsing de la página
                    await fetchParsedData();
                    showLoading(false);
                };
                pageImg.onerror = () => {
                    pageImg.onload = null;
                    pageImg.onerror = null;
                    alert('Error cargando la vista de la página.');
                    showLoading(false);
                };
                pageImg.src = imgUrl;
            }

            // Obtiene la salida directa de parse_pdf
            async function fetchParsedData() {
                try {
                    const res = await fetch(`/api/v1/debug/parsed/${documentId}/page/${currentPage}`);
                    if (!res.ok) throw new Error('Error recuperando la salida del parser.');

                    pageData = await res.json();

                    // Actualizar métricas
                    charCountSpan.textContent = pageData.text_len;
                    blocksCountSpan.textContent = pageData.blocks.length;

                    // Poblar contenidos en pestañas
                    cleanTextContainer.textContent = pageData.text;
                    populateBlocksList(pageData);

                    // Generar capas interactivas SVG
                    renderSVGOverlays(pageData);

                } catch (e) {
                    console.error("Error cargando metadatos estructurados: ", e);
                }
            }

            // Dibuja los elementos del parser en el overlay SVG interactivo
            function renderSVGOverlays(data) {
                svgOverlay.setAttribute('viewBox', `0 0 ${data.width} ${data.height}`);
                svgOverlay.innerHTML = '';

                // Si está oculta la capa o se dibuja en servidor, omitir dibujo en frontend
                if (!showBoxesToggle.checked || renderBackendToggle.checked) return;

                data.blocks.forEach(block => {
                    const [x0, y0, x1, y1] = block.bbox;
                    const w = x1 - x0;
                    const h = y1 - y0;

                    // Grupo contenedor
                    const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                    group.setAttribute('id', `svg-block-${block.index}`);
                    group.setAttribute('class', 'svg-block-group cursor-pointer');
                    group.style.pointerEvents = 'auto';

                    // Rectángulo delimitador
                    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    rect.setAttribute('x', x0);
                    rect.setAttribute('y', y0);
                    rect.setAttribute('width', w);
                    rect.setAttribute('height', h);
                    rect.setAttribute('fill', 'rgba(99, 102, 241, 0.03)'); // indigo transparente
                    rect.setAttribute('stroke', 'rgba(239, 68, 68, 0.7)'); // rojo
                    rect.setAttribute('stroke-width', '1.3');
                    rect.setAttribute('class', 'transition-all duration-200 hover:fill-indigo-500/20 hover:stroke-indigo-400');

                    // Eventos del rect
                    rect.addEventListener('mouseenter', () => highlightBlock(block.index, true));
                    rect.addEventListener('mouseleave', () => {
                        highlightBlock(block.index, false);
                        showTooltip(null);
                    });
                    rect.addEventListener('mousemove', (e) => showTooltip(block, e));
                    rect.addEventListener('click', () => scrollToBlockCard(block.index));

                    group.appendChild(rect);

                    // Círculo y número de orden
                    if (showReadingOrderToggle.checked) {
                        const cx = (x0 + x1) / 2;
                        const cy = (y0 + y1) / 2;

                        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                        circle.setAttribute('cx', cx);
                        circle.setAttribute('cy', cy);
                        circle.setAttribute('r', '8.5');
                        circle.setAttribute('fill', '#fef08a'); // yellow-200
                        circle.setAttribute('stroke', '#16a34a'); // green-600
                        circle.setAttribute('stroke-width', '1.0');
                        group.appendChild(circle);

                        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                        text.setAttribute('x', cx);
                        text.setAttribute('y', cy + 3.0);
                        text.setAttribute('font-size', '9');
                        text.setAttribute('font-family', 'Outfit, sans-serif');
                        text.setAttribute('font-weight', 'bold');
                        text.setAttribute('fill', '#16a34a');
                        text.setAttribute('text-anchor', 'middle');
                        text.textContent = block.index;
                        group.appendChild(text);
                    }

                    // Dibujar sub-bloques (spans) si está activado
                    if (showSpansToggle.checked && block.spans) {
                        block.spans.forEach(span => {
                            if (!span.text.trim()) return;
                            const [sx0, sy0, sx1, sy1] = span.bbox;
                            const sw = sx1 - sx0;
                            const sh = sy1 - sy0;

                            const spanRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                            spanRect.setAttribute('x', sx0);
                            spanRect.setAttribute('y', sy0);
                            spanRect.setAttribute('width', sw);
                            spanRect.setAttribute('height', sh);
                            spanRect.setAttribute('fill', 'none');
                            spanRect.setAttribute('stroke', 'rgba(56, 189, 248, 0.45)'); // sky-400
                            spanRect.setAttribute('stroke-dasharray', '2,1.5');
                            spanRect.setAttribute('stroke-width', '0.7');
                            group.appendChild(spanRect);
                        });
                    }

                    svgOverlay.appendChild(group);
                });
            }

            // Gestiona el tooltip dinámico al flotar sobre el SVG
            function showTooltip(block, e) {
                if (!block) {
                    tooltip.style.display = 'none';
                    return;
                }

                const rect = viewerContainer.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                // Extraer estilos principales de tipografías
                const fonts = Array.from(new Set((block.spans || []).map(s => s.font).filter(Boolean)));
                const sizes = (block.spans || []).map(s => s.size).filter(Boolean);
                const avgSize = sizes.length ? (sizes.reduce((a, b) => a + b, 0) / sizes.length).toFixed(1) : '0';

                tooltip.innerHTML = `
                    <div class="flex items-center justify-between border-b border-slate-800/80 pb-1.5 mb-1.5">
                        <span class="font-bold text-indigo-300">BLOQUE #${block.index}</span>
                        <span class="text-[9px] bg-slate-900 border border-slate-800 text-slate-400 px-1.5 py-0.2 rounded font-mono">B-No: ${block.block_no}</span>
                    </div>
                    <div class="text-[10px] text-slate-500 font-mono mb-2">Bbox: [${block.bbox.map(v => v.toFixed(1)).join(', ')}]</div>
                    <p class="text-slate-200 text-xs italic line-clamp-3 leading-relaxed mb-2 font-mono">"${escapeHTML(block.text)}"</p>
                    <div class="flex flex-wrap gap-1 mt-1">
                        <span class="bg-indigo-950/60 border border-indigo-900/40 text-[9px] text-indigo-300 px-1.5 py-0.5 rounded">${avgSize}pt</span>
                        ${fonts.slice(0, 2).map(f => `<span class="bg-slate-900 border border-slate-800 text-[9px] text-slate-300 px-1.5 py-0.5 rounded truncate max-w-[120px]" title="${f}">${f.split('+').pop()}</span>`).join('')}
                    </div>
                `;

                tooltip.style.display = 'flex';

                // Calcular posición óptima
                const tw = tooltip.offsetWidth || 280;
                const th = tooltip.offsetHeight || 130;
                let left = x + 15;
                let top = y + 15;

                if (left + tw > rect.width) {
                    left = x - tw - 15;
                }
                if (top + th > rect.height) {
                    top = y - th - 15;
                }

                tooltip.style.left = `${left}px`;
                tooltip.style.top = `${top}px`;
            }

            // Sincroniza el resaltado visual entre el SVG y la tarjeta lateral
            function highlightBlock(index, isHighlight) {
                // 1. Resaltado en SVG
                const svgGroup = document.getElementById(`svg-block-${index}`);
                if (svgGroup) {
                    const rect = svgGroup.querySelector('rect');
                    if (rect) {
                        if (isHighlight) {
                            rect.setAttribute('fill', 'rgba(99, 102, 241, 0.15)'); // Indigo
                            rect.setAttribute('stroke', '#6366f1');
                            rect.setAttribute('stroke-width', '2.2');
                        } else {
                            rect.setAttribute('fill', 'rgba(99, 102, 241, 0.03)');
                            rect.setAttribute('stroke', 'rgba(239, 68, 68, 0.7)'); // Rojo original
                            rect.setAttribute('stroke-width', '1.3');
                        }
                    }
                }

                // 2. Resaltado en tarjeta del inspector
                const card = document.getElementById(`block-card-${index}`);
                if (card) {
                    if (isHighlight) {
                        card.classList.add('border-indigo-500/60', 'bg-indigo-950/20', 'shadow-md', 'shadow-indigo-500/5');
                        card.classList.remove('border-slate-800', 'bg-slate-900/40');
                    } else {
                        card.classList.remove('border-indigo-500/60', 'bg-indigo-950/20', 'shadow-md', 'shadow-indigo-500/5');
                        card.classList.add('border-slate-800', 'bg-slate-900/40');
                    }
                }
            }

            // Desplaza la lista lateral hasta el bloque correspondiente
            function scrollToBlockCard(index) {
                // Cambiar a pestaña de Bloques por si estaba en Texto Plano
                tabBlocks.click();

                const card = document.getElementById(`block-card-${index}`);
                if (card) {
                    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }

            // Construye dinámicamente la lista de tarjetas en el inspector lateral
            function populateBlocksList(data) {
                blocksList.innerHTML = '';

                data.blocks.forEach(block => {
                    const card = document.createElement('div');
                    card.setAttribute('id', `block-card-${block.index}`);
                    card.setAttribute('class', 'p-3 rounded-xl border border-slate-800 bg-slate-900/40 hover:bg-slate-950/60 cursor-pointer transition-all duration-300 flex flex-col gap-2 relative group');

                    const uniqueFonts = Array.from(new Set((block.spans || []).map(s => s.font).filter(Boolean)));
                    const fontBadges = uniqueFonts.map(f => `
                        <span class="px-1.5 py-0.5 rounded text-[9px] bg-slate-900 border border-slate-800 text-slate-400 font-mono truncate max-w-[110px]" title="${f}">
                            ${f.split('+').pop()}
                        </span>
                    `).join('');

                    const sizes = (block.spans || []).map(s => s.size).filter(Boolean);
                    const minS = sizes.length ? Math.min(...sizes) : 0;
                    const maxS = sizes.length ? Math.max(...sizes) : 0;
                    const sizeLabel = minS === maxS ? `${minS.toFixed(1)}pt` : `${minS.toFixed(1)}-${maxS.toFixed(1)}pt`;

                    card.innerHTML = `
                        <div class="flex justify-between items-center gap-2">
                            <div class="flex items-center gap-2">
                                <span class="w-5 h-5 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-[10px] font-bold text-indigo-300">
                                    ${block.index}
                                </span>
                                <span class="text-[9px] text-slate-500 font-mono">B-No: ${block.block_no}</span>
                            </div>
                            <span class="text-[9px] font-mono text-indigo-400/80">
                                [${block.bbox.map(v => v.toFixed(0)).join(', ')}]
                            </span>
                        </div>

                        <p class="text-xs text-slate-200 line-clamp-3 leading-relaxed font-mono font-light select-text group-hover:text-white transition-colors">
                            ${escapeHTML(block.text)}
                        </p>

                        <div class="flex flex-wrap gap-1 border-t border-slate-800/60 pt-2">
                            <span class="px-1.5 py-0.5 rounded text-[9px] bg-indigo-950/40 text-indigo-300 border border-indigo-900/30 font-semibold font-mono">
                                ${sizeLabel}
                            </span>
                            ${fontBadges}
                        </div>

                        <!-- Spans Detailed breakdown -->
                        <div class="hidden mt-2 pt-2 border-t border-slate-800/80 flex flex-col gap-1 text-[10px]" id="block-spans-${block.index}">
                            <div class="text-[9px] text-indigo-400 font-semibold mb-1 uppercase tracking-wider">Sub-segmentos de Estilo (Spans):</div>
                            ${(block.spans || []).map((span, sIdx) => {
                                const r = (span.color >> 16) & 255;
                                const g = (span.color >> 8) & 255;
                                const b = span.color & 255;
                                const colorHex = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase();

                                const flags = span.flags;
                                let fBadges = '';
                                if (flags & 1) fBadges += '<span class="px-1 py-0.2 bg-violet-950/60 border border-violet-800/40 text-[8px] text-violet-300 rounded font-mono">sup</span>';
                                if (flags & 2) fBadges += '<span class="px-1 py-0.2 bg-amber-950/60 border border-amber-800/40 text-[8px] text-amber-300 rounded font-mono">italic</span>';
                                if (flags & 4) fBadges += '<span class="px-1 py-0.2 bg-teal-950/60 border border-teal-800/40 text-[8px] text-teal-300 rounded font-mono">serif</span>';
                                if (flags & 8) fBadges += '<span class="px-1 py-0.2 bg-cyan-950/60 border border-cyan-800/40 text-[8px] text-cyan-300 rounded font-mono">mono</span>';
                                if (flags & 16) fBadges += '<span class="px-1 py-0.2 bg-rose-950/60 border border-rose-800/40 text-[8px] text-rose-300 rounded font-mono">bold</span>';

                                return `
                                    <div class="p-1.5 rounded bg-slate-950/30 border border-slate-800/60 hover:border-slate-700/50 flex flex-col gap-1 transition-all">
                                        <div class="text-slate-100 italic select-text">"${escapeHTML(span.text)}"</div>
                                        <div class="flex flex-wrap items-center gap-1.5 text-[8.5px] text-slate-500 font-mono">
                                            <span>${span.size.toFixed(1)}pt</span>
                                            <span>•</span>
                                            <span class="truncate max-w-[90px]" title="${span.font}">${span.font.split('+').pop()}</span>
                                            <span>•</span>
                                            <span class="flex items-center gap-1">
                                                <span class="w-1.5 h-1.5 rounded-full border border-slate-700" style="background-color: rgb(${r},${g},${b})"></span>
                                                ${colorHex}
                                            </span>
                                            ${fBadges ? `<span>•</span><div class="flex gap-0.5">${fBadges}</div>` : ''}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>

                        <!-- Collapse toggler -->
                        <button class="absolute top-2.5 right-2.5 text-slate-500 hover:text-slate-300 transition-colors" onclick="event.stopPropagation(); toggleSpansDetail(${block.index})">
                            <svg class="w-4 h-4 transition-transform duration-300" id="span-arrow-${block.index}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </button>
                    `;

                    // Eventos en tarjetas
                    card.addEventListener('mouseenter', () => highlightBlock(block.index, true));
                    card.addEventListener('mouseleave', () => highlightBlock(block.index, false));
                    card.addEventListener('click', () => {
                        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        
                        // Efecto de pulso en SVG overlay
                        const svgGroup = document.getElementById(`svg-block-${block.index}`);
                        if (svgGroup) {
                            const r = svgGroup.querySelector('rect');
                            if (r) {
                                r.classList.add('pulse-highlight');
                                setTimeout(() => r.classList.remove('pulse-highlight'), 1200);
                            }
                        }
                    });

                    blocksList.appendChild(card);
                });
            }

            // Control de colapso de spans detallados
            window.toggleSpansDetail = function(index) {
                const sp = document.getElementById(`block-spans-${index}`);
                const arr = document.getElementById(`span-arrow-${index}`);
                if (sp.classList.contains('hidden')) {
                    sp.classList.remove('hidden');
                    arr.classList.add('rotate-180');
                } else {
                    sp.classList.add('hidden');
                    arr.classList.remove('rotate-180');
                }
            }

            // Helpers y Paginación
            function updatePaginationUI() {
                pageInput.value = currentPage;
                pageInput.max = totalPages;
                totalPagesSpan.textContent = totalPages;

                prevBtn.disabled = currentPage <= 1;
                nextBtn.disabled = currentPage >= totalPages;
            }

            prevBtn.addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    updatePaginationUI();
                    loadPageImage();
                }
            });

            nextBtn.addEventListener('click', () => {
                if (currentPage < totalPages) {
                    currentPage++;
                    updatePaginationUI();
                    loadPageImage();
                }
            });

            pageInput.addEventListener('change', (e) => {
                let pageVal = parseInt(e.target.value);
                if (isNaN(pageVal) || pageVal < 1) {
                    pageVal = 1;
                } else if (pageVal > totalPages) {
                    pageVal = totalPages;
                }
                currentPage = pageVal;
                updatePaginationUI();
                loadPageImage();
            });

            function showLoading(show) {
                if (show) {
                    loadingOverlay.classList.remove('opacity-0', 'pointer-events-none');
                } else {
                    loadingOverlay.classList.add('opacity-0', 'pointer-events-none');
                }
            }

            function escapeHTML(str) {
                if (!str) return '';
                return str.replace(/&/g, '&amp;')
                          .replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;')
                          .replace(/"/g, '&quot;')
                          .replace(/'/g, '&#039;');
            }

            // Control de pestañas del Inspector lateral
            tabBlocks.addEventListener('click', () => {
                tabBlocks.classList.add('border-indigo-500', 'text-indigo-400');
                tabBlocks.classList.remove('text-slate-400', 'border-transparent');
                tabText.classList.remove('border-indigo-500', 'text-indigo-400');
                tabText.classList.add('text-slate-400', 'border-transparent');

                blocksList.style.display = 'flex';
                cleanTextContainer.style.display = 'none';
            });

            tabText.addEventListener('click', () => {
                tabText.classList.add('border-indigo-500', 'text-indigo-400');
                tabText.classList.remove('text-slate-400', 'border-transparent');
                tabBlocks.classList.remove('border-indigo-500', 'text-indigo-400');
                tabBlocks.classList.add('text-slate-400', 'border-transparent');

                blocksList.style.display = 'none';
                cleanTextContainer.style.display = 'block';
            });

            // Configurar los listeners en controles de capas
            [showBoxesToggle, showReadingOrderToggle, showSpansToggle, renderBackendToggle].forEach(t => {
                t.addEventListener('change', () => {
                    localStorage.setItem(t.id, t.checked);
                    if (t.id === 'renderBackendToggle') {
                        loadPageImage();
                    } else {
                        if (pageData) renderSVGOverlays(pageData);
                    }
                });
            });

            function initToggles() {
                [showBoxesToggle, showReadingOrderToggle, showSpansToggle, renderBackendToggle].forEach(t => {
                    const saved = localStorage.getItem(t.id);
                    if (saved !== null) {
                        t.checked = saved === 'true';
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

