# Plan de Implementación: Spec 8 - Interfaz de Chat y Referencias

Este plan detalla la estrategia de ejecución paso a paso para implementar el chat lateral de IA en streaming, el flujo de ingesta asíncrona de PDFs y el visor interactivo de referencias bibliográficas.

---

## 1. Estrategia de Ejecución (Paso a Paso)

### Paso 1: Extender el Puente C++ (JSBridge)
1. **Modificar `/visor/src/jsbridge.h`:**
   - Declarar slots `getFileHash()`, `ingestDocument()` y `scrollToPage()`.
   - Declarar señales `ingestStatus()` y `pageNavigationRequested()`.
2. **Modificar `/visor/src/jsbridge.cpp`:**
   - Implementar `getFileHash` abriendo el archivo local y aplicando `QCryptographicHash(Sha256)`.
   - Implementar `ingestDocument` utilizando `QNetworkAccessManager` y `QHttpMultiPart` para enviar el archivo local a `/api/v1/documents/upload` de forma asíncrona.
   - Conectar el progreso del upload a la señal `ingestStatus(..., "processing", progress, ...)`.
   - Conectar la finalización al slot para emitir `ingestStatus(..., "completed", ...)` o `"error"`.
   - Implementar `scrollToPage` emitiendo `pageNavigationRequested(pageNumber)`.

### Paso 2: Integrar Navegación en MainWindow
1. **Modificar `/visor/src/mainwindow.h`:**
   - Declarar el slot `scrollToPage(int pageNumber)`.
2. **Modificar `/visor/src/mainwindow.cpp`:**
   - Conectar la señal `m_bridge->pageNavigationRequested` al slot `MainWindow::scrollToPage`.
   - Implementar `MainWindow::scrollToPage` cargando `m_part->openUrl(QUrl::fromLocalFile(m_currentFilePath) + QString("#%1").arg(pageNumber))`.
   - Actualizar `MainWindow::openDocument(const QString &filePath)` para calcular el hash SHA-256 local llamando a `m_bridge->getFileHash(filePath)` y emitir `m_bridge->fileLoaded(filePath, documentId)` a través del puente WebChannel.

### Paso 3: Crear el Componente de Chat en React
1. **Crear `/frontend/src/components/ChatPanel.tsx`:**
   - Mantener estado de mensajes (`messages`), texto de entrada (`inputText`), y estado de conexión y carga.
   - Implementar `fetchHistory(documentId)` llamando a `GET /api/v1/chat/history/{documentId}`.
   - Implementar `clearHistory(documentId)` llamando a `DELETE /api/v1/chat/history/{documentId}`.
   - Implementar `handleSend()` consumiendo `POST /api/v1/chat/message` en modo streaming usando `fetch` y `ReadableStream`.
   - Formatear el texto de respuestas para transformar patrones `[X]` en elementos cliqueables `<span class="citation">[X]</span>`.
   - Al pasar el cursor o hacer clic sobre una cita `[X]`, consultar el metadato bibliográfico y mostrar un popover flotante con el detalle de la fuente citada y un botón de navegación que llame a `window.qtBridge.scrollToPage(pageNum)`.

### Paso 4: Conectar ChatPanel en App.tsx
1. **Modificar `/frontend/src/App.tsx`:**
   - Escuchar señal de C++ `fileLoaded(filePath, documentId)`.
   - Consultar si el documento ya está indexado consultando `GET /api/v1/documents/chunks/{documentId}`.
   - Si no está indexado, mostrar una tarjeta de bienvenida y el botón *"Procesar Documento"*.
   - Al hacer clic en *"Procesar"*, invocar `window.qtBridge.ingestDocument(filePath, documentId)`.
   - Escuchar señal `ingestStatus` para mostrar una barra de progreso. Al completarse, refrescar el estado para cargar el `ChatPanel`.

### Paso 5: Compilación y Verificación Completa
1. Compilar el visor C++.
2. Asegurar que FastAPI local (`localhost:8000`) esté corriendo con LanceDB.
3. Iniciar el frontend React con `npm run dev`.
4. Cargar un PDF desde el visor.
5. Ingestar el PDF si no está indexado, ver el progreso de carga y chatear con la IA observando las respuestas en tiempo real (streaming).
6. Verificar que hacer clic en una cita desplaza el PDF a la página correspondiente.

---

## 2. Plan de Asignación y Paralelización
La tarea será implementada de forma directa y secuencial por el agente principal, garantizando la consistencia en el protocolo de red y el canal de mensajería IPC. No se requiere paralelización con subagentes en esta etapa.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Tras recibir la aprobación del plan de desarrollo:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Procederemos a realizar las modificaciones e integraciones del visor y de React.
