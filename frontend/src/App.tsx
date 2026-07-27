import { useEffect, useState } from "react";
import { initWebChannel } from "./qwebchannel";
import { ChatPanel } from "./components/ChatPanel";
import { LibraryGraph } from "./components/LibraryGraph";

interface NodeData {
  id: string;
  label: string;
  pages_count: number;
  reading_progress: number;
  added_at: string;
  tags?: string[];
  chunks_count?: number;
}

interface EdgeData {
  source: string;
  target: string;
  similarity: number;
}

function App() {
  const [route, setRoute] = useState(window.location.pathname);
  const [isConnected, setIsConnected] = useState(false);
  const [currentFile, setCurrentFile] = useState<string>("Ninguno");
  const [documentId, setDocumentId] = useState<string>("");
  const [isIndexed, setIsIndexed] = useState<boolean>(false);
  
  // Estados para la biblioteca y el grafo
  const [libraryDocs, setLibraryDocs] = useState<NodeData[]>([]);
  const [graphNodes, setGraphNodes] = useState<NodeData[]>([]);
  const [graphEdges, setGraphEdges] = useState<EdgeData[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState("Todos");
  const [similarityThreshold, setSimilarityThreshold] = useState(0.6);
  const [selectedDoc, setSelectedDoc] = useState<NodeData | null>(null);
  
  // Estados para añadir tags
  const [newTagInput, setNewTagInput] = useState("");

  // Estados para el progreso de la ingesta
  const [ingestState, setIngestState] = useState<"idle" | "processing" | "completed" | "error">("idle");
  const [ingestProgress, setIngestProgress] = useState<number>(0);
  const [ingestError, setIngestError] = useState<string>("");

  useEffect(() => {
    // Escuchar cambios de ruta de forma manual para soporte de navegación simple
    const handleLocationChange = () => {
      setRoute(window.location.pathname);
    };
    window.addEventListener("popstate", handleLocationChange);

    // Inicializar puente IPC
    initWebChannel(async (bridge) => {
      setIsConnected(true);
      
      // Conectar la señal de archivo cargado (filePath + documentId/hash)
      bridge.fileLoaded.connect((filePath: string, docId: string) => {
        setCurrentFile(filePath);
        setDocumentId(docId);
        setIngestState("idle");
        setIngestProgress(0);
        setIngestError("");
        
        // Verificar si el documento ya está indexado en el backend
        checkIfIndexed(docId);
      });

      // Conectar la señal de estado de la ingesta
      bridge.ingestStatus.connect((docId: string, status: string, progress: number, error: string) => {
        setDocumentId(docId);
        if (status === "processing") {
          setIngestState("processing");
          setIngestProgress(progress);
        } else if (status === "completed") {
          setIngestState("completed");
          setIngestProgress(1);
          setIsIndexed(true);
          // Recargar biblioteca tras la ingesta exitosa
          fetchLibraryData();
        } else if (status === "error") {
          setIngestState("error");
          setIngestError(error);
        }
      });

      // Consulta de carga inicial para evitar race conditions
      try {
        const filePath = await bridge.currentFilePath();
        const docId = await bridge.currentDocumentId();
        if (filePath && filePath !== "Ninguno" && docId) {
          setCurrentFile(filePath);
          setDocumentId(docId);
          checkIfIndexed(docId);
        }
      } catch (err) {
        console.error("Error cargando el archivo inicial desde el puente:", err);
      }
    });

    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, []);

  // Cargar datos de biblioteca al activar la ruta de biblioteca
  useEffect(() => {
    if (route === "/library") {
      fetchLibraryData();
    }
  }, [route]);

  const fetchLibraryData = async () => {
    try {
      const docsRes = await fetch("http://localhost:8000/api/v1/library/documents");
      if (docsRes.ok) {
        const docs = await docsRes.json();
        const formattedDocs = docs.map((d: any) => ({
          id: d.document_id,
          label: d.filename,
          pages_count: d.pages_count,
          reading_progress: d.reading_progress || 0.0,
          added_at: d.added_at,
          tags: d.tags || [],
          chunks_count: d.chunks_count || 0,
        }));
        setLibraryDocs(formattedDocs);
      }

      const graphRes = await fetch("http://localhost:8000/api/v1/library/graph");
      if (graphRes.ok) {
        const graph = await graphRes.json();
        setGraphNodes(graph.nodes || []);
        setGraphEdges(graph.edges || []);
      }
    } catch (err) {
      console.error("Error fetching library data:", err);
    }
  };

  const checkIfIndexed = async (docId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/documents/chunks/${docId}`);
      if (response.ok) {
        setIsIndexed(true);
      } else {
        setIsIndexed(false);
      }
    } catch (error) {
      console.error("Error al consultar indexación de documento:", error);
      setIsIndexed(false);
    }
  };

  const handleStartIngest = () => {
    if (window.qtBridge && currentFile !== "Ninguno" && documentId) {
      setIngestState("processing");
      setIngestProgress(0);
      window.qtBridge.ingestDocument(currentFile, documentId);
    }
  };

  const handleOpenInVisor = async (docId: string) => {
    if (window.qtBridge) {
      try {
        await window.qtBridge.openDocumentFromReact(docId);
        await window.qtBridge.setCurrentTab(0); // Cambiar a la pestaña del Visor
      } catch (err) {
        console.error("Error abriendo documento desde React:", err);
      }
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (confirm("¿Estás seguro de que deseas eliminar este documento de tu biblioteca?")) {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/library/documents/${docId}`, {
          method: "DELETE",
        });
        if (response.ok) {
          if (selectedDoc?.id === docId) {
            setSelectedDoc(null);
          }
          fetchLibraryData();
        }
      } catch (err) {
        console.error("Error al eliminar documento:", err);
      }
    }
  };

  const handleUpdateProgress = async (docId: string, progress: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/library/documents/${docId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reading_progress: progress }),
      });
      if (response.ok) {
        // Actualizar estados locales
        setLibraryDocs((prev) =>
          prev.map((d) => (d.id === docId ? { ...d, reading_progress: progress } : d))
        );
        setGraphNodes((prev) =>
          prev.map((d) => (d.id === docId ? { ...d, reading_progress: progress } : d))
        );
        if (selectedDoc && selectedDoc.id === docId) {
          setSelectedDoc((prev) => (prev ? { ...prev, reading_progress: progress } : null));
        }
      }
    } catch (err) {
      console.error("Error actualizando progreso de lectura:", err);
    }
  };

  const handleAddTag = async (e: React.FormEvent, docId: string) => {
    e.preventDefault();
    if (!newTagInput.trim()) return;

    const doc = libraryDocs.find((d) => d.id === docId);
    if (!doc) return;

    const updatedTags = Array.from(new Set([...(doc.tags || []), newTagInput.trim()]));

    try {
      const response = await fetch(`http://localhost:8000/api/v1/library/documents/${docId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tags: updatedTags }),
      });
      if (response.ok) {
        setNewTagInput("");
        // Actualizar estados locales
        setLibraryDocs((prev) =>
          prev.map((d) => (d.id === docId ? { ...d, tags: updatedTags } : d))
        );
        if (selectedDoc && selectedDoc.id === docId) {
          setSelectedDoc((prev) => (prev ? { ...prev, tags: updatedTags } : null));
        }
      }
    } catch (err) {
      console.error("Error al añadir tag:", err);
    }
  };

  const handleRemoveTag = async (docId: string, tagToRemove: string) => {
    const doc = libraryDocs.find((d) => d.id === docId);
    if (!doc) return;

    const updatedTags = (doc.tags || []).filter((t) => t !== tagToRemove);

    try {
      const response = await fetch(`http://localhost:8000/api/v1/library/documents/${docId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tags: updatedTags }),
      });
      if (response.ok) {
        setLibraryDocs((prev) =>
          prev.map((d) => (d.id === docId ? { ...d, tags: updatedTags } : d))
        );
        if (selectedDoc && selectedDoc.id === docId) {
          setSelectedDoc((prev) => (prev ? { ...prev, tags: updatedTags } : null));
        }
      }
    } catch (err) {
      console.error("Error al remover tag:", err);
    }
  };

  const handleSelectNodeFromGraph = (nodeId: string) => {
    const doc = libraryDocs.find((d) => d.id === nodeId);
    if (doc) {
      setSelectedDoc(doc);
    }
  };

  const renderChat = () => {
    if (currentFile === "Ninguno") {
      return (
        <div className="panel-container">
          <header className="panel-header">
            <h2>Asistente de Lectura</h2>
            <span className={`status-badge ${isConnected ? "online" : "offline"}`}>
              {isConnected ? "Conectado" : "Desconectado"}
            </span>
          </header>
          <main className="panel-content">
            <div className="chat-welcome" style={{ margin: "auto" }}>
              <h4>Visor Listo</h4>
              <p>Abre un documento PDF desde el visor para comenzar a chatear e interactuar con la IA.</p>
            </div>
          </main>
        </div>
      );
    }

    if (!isIndexed) {
      const filename = currentFile.split("/").pop();
      return (
        <div className="panel-container">
          <header className="panel-header">
            <h2>Asistente de Lectura</h2>
            <span className={`status-badge ${isConnected ? "online" : "offline"}`}>
              {isConnected ? "Conectado" : "Desconectado"}
            </span>
          </header>
          <main className="panel-content">
            <div className="ingest-card">
              <h3>Documento no Indexado</h3>
              <p>El archivo <strong>{filename}</strong> no ha sido procesado aún en tu biblioteca.</p>
              
              {ingestState === "idle" && (
                <button className="primary-btn" onClick={handleStartIngest}>
                  Procesar Documento
                </button>
              )}

              {ingestState === "processing" && (
                <div>
                  <div className="progress-container">
                    <div 
                      className="progress-bar" 
                      style={{ width: `${Math.round(ingestProgress * 100)}%` }} 
                    />
                  </div>
                  <span className="progress-label">
                    Procesando: {Math.round(ingestProgress * 100)}%
                  </span>
                </div>
              )}

              {ingestState === "error" && (
                <div>
                  <div className="error-message">
                    <strong>Error de carga:</strong> {ingestError}
                  </div>
                  <button className="primary-btn" style={{ marginTop: "12px" }} onClick={handleStartIngest}>
                    Reintentar Procesamiento
                  </button>
                </div>
              )}
            </div>
          </main>
        </div>
      );
    }

    return <ChatPanel documentId={documentId} filePath={currentFile} />;
  };

  // Obtener tags únicos de toda la biblioteca para el filtro
  const allUniqueTags = Array.from(new Set(libraryDocs.flatMap((d) => d.tags || [])));

  // Filtrar documentos de la tabla por buscador y tag seleccionado
  const filteredDocs = libraryDocs.filter((doc) => {
    const matchesSearch = doc.label.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTag = selectedTag === "Todos" || (doc.tags || []).includes(selectedTag);
    return matchesSearch && matchesTag;
  });

  const renderLibrary = () => (
    <div className="panel-container library-layout-full">
      <header className="panel-header">
        <div className="header-left">
          <h2>Biblioteca Digital</h2>
          <span className={`status-badge ${isConnected ? "online" : "offline"}`}>
            {isConnected ? "Conectado" : "Desconectado"}
          </span>
        </div>
        <div className="header-controls">
          <input
            type="text"
            placeholder="Buscar por nombre..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="tag-select"
          >
            <option value="Todos">Todas las etiquetas</option>
            {allUniqueTags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
        </div>
      </header>

      <main className="library-main-grid">
        {/* Panel Izquierdo: Tabla de Documentos */}
        <section className="library-left-panel">
          <div className="table-wrapper">
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Documento</th>
                  <th style={{ width: "80px" }}>Páginas</th>
                  <th>Progreso</th>
                  <th style={{ width: "110px", textAlign: "right" }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="empty-table-text">
                      No hay documentos que coincidan con la búsqueda.
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => (
                    <tr
                      key={doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      className={`table-row ${selectedDoc?.id === doc.id ? "selected" : ""}`}
                    >
                      <td className="doc-name-cell">
                        <div className="doc-title">{doc.label}</div>
                        <div className="doc-tags-pills">
                          {doc.tags?.map((t) => (
                            <span key={t} className="tag-pill">
                              {t}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td style={{ textAlign: "center" }}>{doc.pages_count}</td>
                      <td>
                        <div className="progress-cell">
                          <div className="progress-bar-small-bg">
                            <div
                              className="progress-bar-small-fill"
                              style={{ width: `${Math.round(doc.reading_progress * 100)}%` }}
                            />
                          </div>
                          <span className="progress-percent">
                            {Math.round(doc.reading_progress * 100)}%
                          </span>
                        </div>
                      </td>
                      <td className="actions-cell" style={{ textAlign: "right" }}>
                        <button
                          className="action-icon-btn open-btn"
                          title="Abrir en Visor"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenInVisor(doc.id);
                          }}
                        >
                          ▶️
                        </button>
                        <button
                          className="action-icon-btn delete-btn"
                          title="Eliminar"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteDoc(doc.id);
                          }}
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Panel Derecho: Grafo y Detalles */}
        <section className="library-right-panel">
          <div className="graph-header-controls">
            <label className="threshold-label">
              Similitud Semántica Mínima:{" "}
              <strong>{Math.round(similarityThreshold * 100)}%</strong>
            </label>
            <input
              type="range"
              min="0.3"
              max="0.95"
              step="0.05"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
              className="threshold-slider"
            />
          </div>

          <div className="graph-box-wrapper">
            {graphNodes.length === 0 ? (
              <div className="graph-placeholder">
                <p>Agrega y procesa documentos para ver el grafo semántico de relaciones.</p>
              </div>
            ) : (
              <LibraryGraph
                nodes={graphNodes}
                edges={graphEdges}
                threshold={similarityThreshold}
                onSelectNode={handleSelectNodeFromGraph}
              />
            )}
          </div>

          {/* Panel de Detalles del Documento Seleccionado */}
          <div className="doc-details-panel">
            {selectedDoc ? (
              <div className="details-card">
                <div className="details-header">
                  <h4>{selectedDoc.label}</h4>
                  <button className="primary-btn open-visor-btn" onClick={() => handleOpenInVisor(selectedDoc.id)}>
                    Cargar en Visor
                  </button>
                </div>

                <div className="details-grid">
                  <div>
                    <span className="details-label">Páginas:</span>{" "}
                    <span className="details-value">{selectedDoc.pages_count}</span>
                  </div>
                  <div>
                    <span className="details-label">Agregado el:</span>{" "}
                    <span className="details-value">
                      {new Date(selectedDoc.added_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Edición de Progreso */}
                <div className="progress-edit-section">
                  <label>Progreso de Lectura:</label>
                  <div className="progress-slider-wrapper">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={selectedDoc.reading_progress}
                      onChange={(e) =>
                        handleUpdateProgress(selectedDoc.id, parseFloat(e.target.value))
                      }
                      className="details-progress-slider"
                    />
                    <span>{Math.round(selectedDoc.reading_progress * 100)}%</span>
                  </div>
                </div>

                {/* Edición de Tags */}
                <div className="tags-edit-section">
                  <label>Etiquetas (Haz clic para eliminar):</label>
                  <div className="details-tags-list">
                    {selectedDoc.tags?.length === 0 ? (
                      <span className="no-tags-text">Sin etiquetas</span>
                    ) : (
                      selectedDoc.tags?.map((t) => (
                        <span
                          key={t}
                          className="tag-pill-editable"
                          title="Eliminar etiqueta"
                          onClick={() => handleRemoveTag(selectedDoc.id, t)}
                        >
                          {t} <span className="remove-cross">×</span>
                        </span>
                      ))
                    )}
                  </div>
                  <form
                    onSubmit={(e) => handleAddTag(e, selectedDoc.id)}
                    className="add-tag-form"
                  >
                    <input
                      type="text"
                      placeholder="Nueva etiqueta..."
                      value={newTagInput}
                      onChange={(e) => setNewTagInput(e.target.value)}
                    />
                    <button type="submit">Añadir</button>
                  </form>
                </div>
              </div>
            ) : (
              <div className="no-doc-selected-placeholder">
                <p>Selecciona un documento en la tabla o en el grafo para editar metadatos o etiquetas.</p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );

  return (
    <div className="app-root">
      {route === "/library" ? renderLibrary() : renderChat()}
    </div>
  );
}

export default App;
