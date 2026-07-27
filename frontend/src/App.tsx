import { useEffect, useState } from "react";
import { initWebChannel } from "./qwebchannel";
import { ChatPanel } from "./components/ChatPanel";

function App() {
  const [route, setRoute] = useState(window.location.pathname);
  const [isConnected, setIsConnected] = useState(false);
  const [currentFile, setCurrentFile] = useState<string>("Ninguno");
  const [documentId, setDocumentId] = useState<string>("");
  const [isIndexed, setIsIndexed] = useState<boolean>(false);
  
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
      setIsIndexed(false); // Asumir no indexado en caso de error
    }
  };

  const handleStartIngest = () => {
    if (window.qtBridge && currentFile !== "Ninguno" && documentId) {
      setIngestState("processing");
      setIngestProgress(0);
      window.qtBridge.ingestDocument(currentFile, documentId);
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

  const renderLibrary = () => (
    <div className="panel-container library-layout">
      <header className="panel-header">
        <h2>Biblioteca Digital</h2>
        <span className={`status-badge ${isConnected ? "online" : "offline"}`}>
          {isConnected ? "Conectado" : "Desconectado"}
        </span>
      </header>

      <main className="panel-content">
        <div className="alert-box">
          <p>Esta es la vista de la Biblioteca (Pestaña 2).</p>
        </div>
        <div className="card">
          <h3>Información del Documento Activo</h3>
          <p><strong>Ruta:</strong> {currentFile}</p>
          <p><strong>ID (Hash):</strong> {documentId || "Ninguno"}</p>
          <p><strong>Estado:</strong> {isIndexed ? "Indexado en Base de Datos" : "No Indexado"}</p>
        </div>
        <div className="chat-welcome">
          <p>El grafo de relaciones semánticas y la tabla interactiva de biblioteca se desarrollarán en la siguiente spec (Spec 9).</p>
        </div>
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
