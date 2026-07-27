import { useEffect, useState } from "react";
import { initWebChannel } from "./qwebchannel";

function App() {
  const [route, setRoute] = useState(window.location.pathname);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [currentFile, setCurrentFile] = useState<string>("Ninguno");

  useEffect(() => {
    // Escuchar cambios de ruta de forma manual para soporte de navegación simple
    const handleLocationChange = () => {
      setRoute(window.location.pathname);
    };
    window.addEventListener("popstate", handleLocationChange);

    // Inicializar puente IPC
    initWebChannel((bridge) => {
      setIsConnected(true);
      
      // Conectar la señal de archivo cargado
      bridge.fileLoaded.connect((filePath: string) => {
        setCurrentFile(filePath);
        setMessages((prev) => [...prev, `Señales C++: Archivo PDF cargado: ${filePath}`]);
      });
    });

    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, []);

  const handleSendMessage = () => {
    if (window.qtBridge) {
      const msg = `Hola desde React (Ruta: ${route}, Hora: ${new Date().toLocaleTimeString()})`;
      window.qtBridge.postMessage(msg);
      setMessages((prev) => [...prev, `Enviado a C++: ${msg}`]);
    } else {
      alert("El puente de comunicación con C++ no está conectado.");
    }
  };

  const renderChat = () => (
    <div className="panel-container">
      <header className="panel-header">
        <h2>Asistente de Lectura</h2>
        <span className={`status-badge ${isConnected ? "online" : "offline"}`}>
          {isConnected ? "Conectado" : "Desconectado"}
        </span>
      </header>
      
      <main className="panel-content">
        <div className="card">
          <h3>Información del PDF</h3>
          <p><strong>Archivo actual:</strong> {currentFile}</p>
        </div>

        <button className="primary-btn" onClick={handleSendMessage}>
          Enviar Mensaje de Prueba a C++
        </button>

        <div className="log-container">
          <h3>Historial del Canal (IPC)</h3>
          {messages.length === 0 ? (
            <p className="placeholder-text">No hay eventos en el canal aún...</p>
          ) : (
            <ul>
              {messages.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );

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
          <p>Esta es la vista de la Biblioteca a pantalla completa (Pestaña 2).</p>
        </div>

        <div className="library-mock">
          <button className="primary-btn" onClick={handleSendMessage}>
            Enviar Mensaje a C++ (Biblioteca)
          </button>
          
          <div className="log-container">
            <h3>Historial del Canal (IPC)</h3>
            {messages.length === 0 ? (
              <p className="placeholder-text">Esperando interacciones...</p>
            ) : (
              <ul>
                {messages.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            )}
          </div>
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
