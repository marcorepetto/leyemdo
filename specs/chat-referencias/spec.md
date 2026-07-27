# Especificación de Requisitos (Spec): Spec 8 - Interfaz de Chat y Referencias

Este documento establece la definición formal de la **Spec 8: Interfaz de Chat y Referencias** según la metodología Spec Driven Development (SDD). Esta especificación define el alcance, comportamiento, flujos de datos e interacciones para el chat lateral de IA, la visualización de referencias bibliográficas interactivas y la ingesta guiada de documentos.

---

## 1. Definición del Problema y Objetivos
El usuario necesita interactuar de manera eficiente con el contenido del PDF que lee. El chat lateral debe:
1. Detectar si el PDF abierto está indexado.
2. Si no lo está, guiar al usuario para ingestar el documento mediante un flujo interactivo y asíncrono.
3. Permitir realizar preguntas sobre el documento actual y obtener respuestas didácticas del Tutor pedagógico ZDP en tiempo real (streaming).
4. Cargar y persistir el historial de mensajes de la base de datos local.
5. Permitir hacer clic en las citas `[X]` generadas por la IA para ver la referencia bibliográfica completa y saltar en el visor a la página exacta del PDF donde se ubica.

---

## 2. Alcance (Límites del Sistema)

### Qué HACE la Spec (In-Scope)
* **Gestión de Carga de PDF e Identificación:**
  - El visor C++ calcula el hash SHA-256 del archivo PDF cargado y lo envía junto con la ruta del archivo en la señal `fileLoaded(filePath, documentId)`.
* **Flujo de Ingesta Guiada:**
  - Si el `documentId` no está indexado en LanceDB (devuelve error 404 al consultar chunks), React muestra una tarjeta *"Documento no indexado"* y un botón *"Procesar"*.
  - Al hacer clic, React invoca el slot `ingestDocument(filePath, documentId)` en C++.
  - C++ lee el archivo local en segundo plano, calcula su tamaño y realiza la carga HTTP POST `/upload` a la API local de FastAPI, notificando el estado a React mediante la señal `ingestStatus(documentId, status, progress, error)`.
  - React muestra una barra de carga estética y actualiza el panel al completarse.
* **Interfaz de Chat Conversacional (React):**
  - Consumo de `POST /api/v1/chat/message` usando EventSource/ReadableStream para soportar respuestas en streaming.
  - Visualización del historial de chat usando `GET /api/v1/chat/history/{document_id}`.
  - Limpieza de historial con `DELETE /api/v1/chat/history/{document_id}`.
  - Renderizado premium de Markdown (usando `react-markdown` u otra alternativa que maneje código, texto y saltos).
  - Formato estético de citas `[1]`, `[2]`, etc.
* **Acción Híbrida de Referencias:**
  - Al pasar el cursor o hacer clic sobre una cita `[X]`, React muestra un tooltip/popover con la descripción completa del libro/paper citado (extraído de los metadatos globales de bibliografía del documento en `GET /api/v1/documents/chunks/{documentId}`).
  - El tooltip incluye un botón *"Ir al PDF"*. Al presionarlo, React envía un mensaje por el puente IPC `scrollToPage(pageNumber)` (o similar) para desplazar el visor de Okular a la página exacta del PDF.

### Qué NO HACE la Spec (Out-of-Scope)
* **No implementa la vista de Biblioteca o Grafo Semántico (Spec 9).**
* **No detecta atajos de selección ni menú contextual en el visor PDF C++ (Spec 10).**

---

## 3. Arquitectura y Flujo de Datos

### Flujo de Datos: Ingesta Guiada de PDF
```mermaid
sequenceDiagram
    participant C++ as Visor C++ (Okular)
    participant React as Panel Chat React
    participant API as FastAPI Backend

    C++->>React: fileLoaded(filePath, documentId)
    React->>API: GET /api/v1/documents/chunks/{documentId}
    API-->>React: 404 Not Found (Documento no indexado)
    React->>React: Mostrar UI "Procesar Documento"
    React->>C++: ingestDocument(filePath, documentId) (IPC Slot)
    C++->>API: POST /api/v1/documents/upload (Multi-part upload)
    loop Estado de procesamiento
        C++->>React: ingestStatus(documentId, "processing", progress)
    end
    API-->>C++: 202 Accepted / Processing Completed
    C++->>React: ingestStatus(documentId, "completed")
    React->>React: Cargar Chat e Historial
```

### Flujo de Datos: Interacción con Citas [X]
1. La IA responde: *"El andamiaje pedagógico se define en [1]..."*.
2. React formatea el texto `[1]` como un enlace interactivo.
3. Al hacer clic en `[1]`, React busca el índice `"1"` en el objeto `bibliography` de metadatos globales del documento.
4. React abre un popover flotante con el texto de la cita (ej: *"Zhou, M., et al. Applications of Voronoi Diagrams..."*).
5. El usuario hace clic en *"Ir a la cita en el PDF"* dentro del popover.
6. React llama a `window.qtBridge.scrollToPage(pageNumber)` (enviando la página de referencias del PDF).
7. C++ recibe el número de página y llama a `m_part->openUrl(QUrl::fromLocalFile(filePath) + "#pageNumber")` (o utiliza la API nativa de Okular para saltar de página).

---

## 4. Próxima Fase (Fase 2: Planificación Técnica)
Una vez aprobada esta especificación por el usuario:
1. Se realizará un **commit en git** con la definición aprobada.
2. Se iniciará la redacción del **Plan Técnico** detallando librerías, cambios en el código de C++ y componentes de chat en React.
