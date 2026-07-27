// Declaración de tipos globales para la integración con Qt 6 WebChannel
declare global {
  interface Window {
    qt?: {
      webChannelTransport: any;
    };
    qtBridge?: {
      // Slots expuestos desde C++ (retornan Promesas en JS/TS)
      postMessage: (msg: string) => Promise<void>;
      
      // Señales expuestas desde C++ (se conectan usando .connect)
      fileLoaded: {
        connect: (callback: (filePath: string) => void) => void;
        disconnect: (callback: (filePath: string) => void) => void;
      };
    };
    QWebChannel?: any;
  }
}

export function initWebChannel(onReady: (bridge: any) => void) {
  if (typeof window !== "undefined") {
    // Si ya está inicializado, llamar al callback de inmediato
    if (window.qtBridge) {
      onReady(window.qtBridge);
      return;
    }

    // Esperar a que la página cargue y el transporte esté listo
    const checkAndInit = () => {
      if (window.qt && window.QWebChannel) {
        new window.QWebChannel(window.qt.webChannelTransport, (channel: any) => {
          window.qtBridge = channel.objects.qtBridge;
          console.log("Conectado exitosamente a Qt WebChannel");
          onReady(window.qtBridge);
        });
      } else {
        console.warn("Qt WebChannel no está disponible en este navegador/entorno.");
      }
    };

    if (document.readyState === "complete") {
      checkAndInit();
    } else {
      window.addEventListener("load", checkAndInit);
    }
  }
}
