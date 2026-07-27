import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

interface ChatPanelProps {
  documentId: string;
  filePath: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatPanel({ documentId, filePath }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [bibliography, setBibliography] = useState<Record<string, string>>({});
  const [refPage, setRefPage] = useState<number>(1);
  const [activeCitation, setActiveCitation] = useState<{
    id: string;
    text: string;
    x: number;
    y: number;
  } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cargar historial y extraer bibliografía al iniciar
  useEffect(() => {
    fetchHistory();
    extractBibliography();
  }, [documentId]);

  // Hacer scroll al final del chat al recibir mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchHistory = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/chat/history/${documentId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (error) {
      console.error("Error al obtener historial de chat:", error);
    }
  };

  const clearHistory = async () => {
    if (confirm("¿Estás seguro de que deseas limpiar el historial de este documento?")) {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/chat/history/${documentId}`, {
          method: "DELETE",
        });
        if (response.ok) {
          setMessages([]);
        }
      } catch (error) {
        console.error("Error al limpiar historial:", error);
      }
    }
  };

  const extractBibliography = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/documents/chunks/${documentId}`);
      if (response.ok) {
        const data = await response.json();
        const chunks = data.chunks || [];
        
        // Intentar deducir la bibliografía analizando los fragmentos
        const bibMap: Record<string, string> = {};
        let highestRefPage = 1;

        // Buscar chunks de la sección References
        const refChunks = chunks.filter((c: any) => 
          (c.section && c.section.toLowerCase().includes("reference")) ||
          (c.section && c.section.toLowerCase().includes("bibliograf")) ||
          c.text.toLowerCase().includes("references\n")
        );

        const targetChunks = refChunks.length > 0 ? refChunks : chunks.slice(-3);

        targetChunks.forEach((chunk: any) => {
          if (chunk.page_number > highestRefPage) {
            highestRefPage = chunk.page_number;
          }
          const lines = chunk.text.split("\n");
          lines.forEach((line: string) => {
            const match = line.match(/^\s*\[?([0-9]+)\]?\.?\s+(.+)$/);
            if (match) {
              bibMap[match[1]] = match[2];
            }
          });
        });

        setBibliography(bibMap);
        setRefPage(highestRefPage);
        console.log(`Bibliografía extraída: ${Object.keys(bibMap).length} entradas. Página de referencias estimada: ${highestRefPage}`);
      }
    } catch (error) {
      console.error("Error al extraer bibliografía:", error);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage = inputText.trim();
    setInputText("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    // Inicializar burbuja vacía para la respuesta de la IA
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const response = await fetch("http://localhost:8000/api/v1/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentId,
          message: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error("Error en la respuesta del servidor de chat.");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");

      if (!reader) {
        throw new Error("No se pudo iniciar el lector de stream.");
      }

      let accumulatedContent = "";
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const cleanLine = line.endsWith("\r") ? line.slice(0, -1) : line;
          if (cleanLine.startsWith("data: ")) {
            const token = cleanLine.slice(6);
            if (token === "[DONE]") continue;
            accumulatedContent += token;
            
            // Actualizar el último mensaje (assistant) en tiempo real
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: accumulatedContent,
                };
              }
              return updated;
            });
          }
        }
      }
    } catch (error: any) {
      console.error("Error en streaming:", error);
      setMessages((prev) => {
        const updated = [...prev];
        if (updated.length > 0) {
          updated[updated.length - 1] = {
            role: "assistant",
            content: `\n[Error de comunicación: ${error.message}]`,
          };
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCitationClick = (e: React.MouseEvent, citId: string) => {
    e.preventDefault();
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    const text = bibliography[citId] || "Detalle de referencia no encontrado.";
    
    setActiveCitation({
      id: citId,
      text,
      x: rect.left,
      y: rect.top + window.scrollY,
    });
  };

  const navigateToReferences = () => {
    if (window.qtBridge) {
      window.qtBridge.scrollToPage(refPage);
      setActiveCitation(null);
    }
  };

  // Preprocesar el texto para convertir "[X]" en links Markdown del tipo "[X](citation:X)"
  const preprocessMarkdown = (text: string) => {
    return text.replace(/\[(\d+)\]/g, "[$1](citation:$1)");
  };

  return (
    <div className="chat-panel">
      <header className="chat-header">
        <div className="title-area">
          <h3>Asistente IA</h3>
          <p className="subtitle">{filePath.split("/").pop()}</p>
        </div>
        <button className="clear-btn" title="Limpiar historial" onClick={clearHistory}>
          🗑️ Limpiar
        </button>
      </header>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <h4>¡Hola! Soy tu tutor de lectura.</h4>
            <p>Pregúntame sobre el contenido de este documento. Te guiaré paso a paso usando andamiaje pedagógico (ZDP) para que comprendas mejor las ideas clave.</p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`chat-bubble-container ${msg.role}`}>
              <div className="chat-avatar">{msg.role === "user" ? "Tú" : "IA"}</div>
              <div className="chat-bubble">
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    a: ({ href, children }) => {
                      if (href && href.startsWith("citation:")) {
                        const citId = href.split(":")[1];
                        return (
                          <span
                            className="citation-link"
                            onClick={(e) => handleCitationClick(e, citId)}
                          >
                            [{citId}]
                          </span>
                        );
                      }
                      return (
                        <a href={href} target="_blank" rel="noopener noreferrer">
                          {children}
                        </a>
                      );
                    },
                  }}
                >
                  {preprocessMarkdown(msg.content)}
                </ReactMarkdown>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {activeCitation && (
        <div
          className="citation-popover"
          style={{
            top: `${activeCitation.y - 120}px`,
            left: `${Math.min(activeCitation.x, window.innerWidth - 320)}px`,
          }}
        >
          <div className="popover-header">
            <h4>Referencia [{activeCitation.id}]</h4>
            <button className="close-popover" onClick={() => setActiveCitation(null)}>
              ×
            </button>
          </div>
          <div className="popover-body">
            <p>{activeCitation.text}</p>
          </div>
          <div className="popover-footer">
            <button className="nav-pdf-btn" onClick={navigateToReferences}>
              📄 Ir a Referencia en PDF (Pág. {refPage})
            </button>
          </div>
        </div>
      )}

      <form className="chat-input-area" onSubmit={handleSend}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={isLoading ? "Tutor escribiendo..." : "Haz una pregunta sobre el texto..."}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !inputText.trim()}>
          {isLoading ? "..." : "Enviar"}
        </button>
      </form>
    </div>
  );
}
