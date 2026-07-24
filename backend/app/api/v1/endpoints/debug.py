# ruff: noqa: E501
import hashlib

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse, Response

from app.services.pdf_debug import draw_debug_annotations

router = APIRouter()

# Caché temporal en memoria de archivos subidos para depuración
DEBUG_PDF_CACHE = {}


@router.post("/upload")
async def upload_debug_pdf(file: UploadFile = File(...)):
    """Sube un archivo PDF temporalmente en memoria para su visualización y depuración."""
    if not file.filename.endswith(".pdf"):
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
    }

    return {"document_id": document_id, "pages_count": pages_count}


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


@router.get("/ui", response_class=HTMLResponse)
def get_debug_ui():
    """Sirve la interfaz web responsiva y moderna para la visualización del depurador."""
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Parser Debugger</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        fontFamily: {
                            sans: ['Outfit', 'sans-serif'],
                        }
                    }
                }
            }
        </script>
        <style>
            body {
                background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            }
            .glassmorphism {
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        </style>
    </head>
    <body class="min-h-screen text-slate-100 flex flex-col font-sans">
        <!-- Header -->
        <header class="w-full glassmorphism py-4 px-8 flex justify-between items-center shadow-lg border-b border-indigo-500/20">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center font-bold text-xl shadow-lg shadow-indigo-500/30">
                    D
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-violet-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">PDF Parser Debugger</h1>
                    <p class="text-xs text-indigo-400/80">Visualizador de Bloques de Lectura & Ordenación 2D</p>
                </div>
            </div>
            <div class="text-xs font-semibold px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                Spec: Debug PDF Parser
            </div>
        </header>

        <!-- Main Body -->
        <main class="flex-1 flex flex-col md:flex-row p-6 gap-6 max-w-7xl mx-auto w-full h-[calc(100vh-100px)] overflow-hidden">
            <!-- Sidebar (Controls) -->
            <section class="w-full md:w-80 flex flex-col gap-4 shrink-0">
                <!-- Upload Box -->
                <div class="glassmorphism rounded-2xl p-5 shadow-xl flex flex-col gap-3">
                    <h2 class="font-semibold text-sm uppercase tracking-wider text-indigo-400">Subir PDF</h2>
                    <div id="dropzone" class="border-2 border-dashed border-indigo-500/30 hover:border-indigo-400 rounded-xl p-6 text-center cursor-pointer transition-all duration-300 bg-slate-900/50 hover:bg-slate-900/80 flex flex-col items-center justify-center group">
                        <svg class="w-10 h-10 text-indigo-400/60 group-hover:text-indigo-400 transition-colors mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"/>
                        </svg>
                        <p class="text-xs text-slate-300 font-medium">Arrastra tu PDF aquí o haz clic para buscar</p>
                        <input type="file" id="fileInput" accept=".pdf" class="hidden">
                    </div>
                </div>

                <!-- Page Navigator -->
                <div id="controlsCard" class="glassmorphism rounded-2xl p-5 shadow-xl flex flex-col gap-4 opacity-50 pointer-events-none transition-opacity duration-300">
                    <h2 class="font-semibold text-sm uppercase tracking-wider text-indigo-400">Paginación</h2>
                    <div class="flex items-center justify-between gap-3">
                        <button id="prevBtn" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold transition-all shadow-md shadow-indigo-600/20 disabled:opacity-30 disabled:pointer-events-none flex-1">
                            Anterior
                        </button>
                        <button id="nextBtn" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold transition-all shadow-md shadow-indigo-600/20 disabled:opacity-30 disabled:pointer-events-none flex-1">
                            Siguiente
                        </button>
                    </div>
                    <div class="flex items-center justify-center gap-2">
                        <span class="text-sm text-slate-400">Pág.</span>
                        <input type="number" id="pageInput" min="1" value="1" class="w-16 bg-slate-900/60 border border-slate-700 rounded-lg px-2 py-1 text-center font-bold text-sm text-indigo-300 focus:outline-none focus:border-indigo-500">
                        <span class="text-sm text-slate-400">de <span id="totalPages" class="font-bold text-slate-200">1</span></span>
                    </div>
                </div>

                <!-- Legend Card -->
                <div class="glassmorphism rounded-2xl p-5 shadow-xl flex flex-col gap-3">
                    <h2 class="font-semibold text-sm uppercase tracking-wider text-indigo-400">Leyenda Visual</h2>
                    <ul class="text-xs text-slate-300 flex flex-col gap-2">
                        <li class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded bg-red-500 inline-block"></span>
                            <span>Caja del Bloque (PyMuPDF)</span>
                        </li>
                        <li class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded bg-blue-500 inline-block"></span>
                            <span>Coordenadas (x0, y0) / (x1, y1)</span>
                        </li>
                        <li class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full bg-yellow-200 border border-green-700 inline-block"></span>
                            <span>Orden Secuencial de Lectura 2D</span>
                        </li>
                    </ul>
                </div>
            </section>

            <!-- Viewer Area -->
            <section class="flex-1 glassmorphism rounded-2xl p-4 shadow-xl flex flex-col items-center justify-center min-h-[300px] overflow-hidden relative">
                <!-- Welcome/State Overlay -->
                <div id="noDocState" class="flex flex-col items-center justify-center text-center p-8 transition-opacity duration-300">
                    <div class="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-inner mb-4">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-slate-200 mb-2">Ningún Documento Cargado</h3>
                    <p class="text-sm text-slate-400 max-w-sm">Sube un paper PDF usando la barra de herramientas lateral para iniciar el diagnóstico visual del algoritmo de ordenación.</p>
                </div>

                <!-- Loader -->
                <div id="loadingOverlay" class="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center transition-all duration-300 opacity-0 pointer-events-none z-10">
                    <div class="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3"></div>
                    <p class="text-sm font-medium text-slate-300">Depurando página y renderizando imagen...</p>
                </div>

                <!-- Page Image Display -->
                <div id="viewerWrapper" class="w-full h-full hidden flex items-center justify-center overflow-auto p-2">
                    <img id="pageImg" class="max-w-full max-h-full object-contain rounded border border-slate-800 shadow-2xl transition-all duration-300" src="" alt="Página del PDF anotada">
                </div>
            </section>
        </main>

        <script>
            // Elementos DOM
            const dropzone = document.getElementById('dropzone');
            const fileInput = document.getElementById('fileInput');
            const controlsCard = document.getElementById('controlsCard');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const pageInput = document.getElementById('pageInput');
            const totalPagesSpan = document.getElementById('totalPages');
            const noDocState = document.getElementById('noDocState');
            const loadingOverlay = document.getElementById('loadingOverlay');
            const viewerWrapper = document.getElementById('viewerWrapper');
            const pageImg = document.getElementById('pageImg');

            // Estado global
            let documentId = '';
            let totalPages = 1;
            let currentPage = 1;

            // Manejo de carga de archivos
            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.classList.add('border-indigo-400', 'bg-slate-900/80');
            });
            dropzone.addEventListener('dragleave', () => {
                dropzone.classList.remove('border-indigo-400', 'bg-slate-900/80');
            });
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('border-indigo-400', 'bg-slate-900/80');
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
                if (!file || file.type !== 'application/pdf') {
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
                    currentPage = 1;

                    // Habilitar controles
                    controlsCard.classList.remove('opacity-50', 'pointer-events-none');
                    noDocState.classList.add('hidden');
                    viewerWrapper.classList.remove('hidden');

                    updatePaginationUI();
                    await loadPageImage();

                } catch (error) {
                    console.error(error);
                    alert('Error cargando el PDF al servidor.');
                    showLoading(false);
                }
            }

            // Cargar imagen de la página anotada
            async function loadPageImage() {
                if (!documentId) return;
                showLoading(true);

                const imgUrl = `/api/v1/debug/view/${documentId}/page/${currentPage}`;

                // Cargar imagen de forma asíncrona para ocultar el loader solo al finalizar
                const tempImg = new Image();
                tempImg.src = imgUrl;
                tempImg.onload = () => {
                    pageImg.src = imgUrl;
                    showLoading(false);
                };
                tempImg.onerror = () => {
                    alert('Error renderizando la página.');
                    showLoading(false);
                };
            }

            // Paginación y botones
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
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
