# Propuesta Técnica: Lector de PDF Inteligente con IA (Basado en Okular)

Este documento describe la arquitectura, stack tecnológico y funcionalidades principales del Lector de PDF Inteligente, según las decisiones de diseño acordadas.

---

## 1. Arquitectura de Integración (Híbrida C++/Qt + React)

El sistema se compone de tres capas principales diseñadas para combinar la velocidad de un visor nativo con la flexibilidad de una interfaz moderna de IA:

### A. Capa de Presentación (Visor y Paneles)
* **Visor PDF (Base Nativa):** Se utilizará un fork de **Okular (C++ / Qt)** como núcleo del visor. Esto proporciona visualización fluida, soporte multiformato, renderizado rápido y herramientas de anotación nativas (subrayado, notas, marcadores) sin necesidad de desarrollar un visor desde cero.
* **Paneles de Asistencia (React + TypeScript):** Para el chat lateral, la visualización de la biblioteca en forma de grafo y tabla, se embeberá un frontend web mediante **QWebEngineView** (motor Chromium integrado en Qt).
* **Puente de Comunicación (IPC):** Se usará **Qt WebChannel** para sincronizar eventos bidireccionales en tiempo real entre el visor C++ y los paneles de React (ej: hacer clic en una cita en el chat hará que Okular resalte y salte a la página y línea del PDF original).

### B. Capa de Control y RAG (FastAPI Sidecar)
* **Servicio Sidecar (Python / FastAPI):** Un backend local que corre en segundo plano y se comunica con los paneles de React y Okular mediante REST/WebSockets.
* **Procesamiento de Documentos:** Ingesta de PDFs, extracción de texto estructurado y división semántica en fragmentos (*chunking*).
* **Base de Datos Vectorial Local:** Almacenamiento local de embeddings utilizando una base de datos vectorial embebida (ej. **LanceDB** o **SQLite-vec**) para realizar búsquedas semánticas rápidas.

### C. Capa de IA (Modelos)
* **Proveedor Principal:** **Google Gemini API** (modelo **Gemini 1.5 Flash**) utilizando una API Key del usuario.
* **Ventajas de Gemini 1.5 Flash:**
  * Contexto gigante de 1 millón de tokens (permite procesar libros enteros y múltiples documentos de soporte simultáneamente).
  * Capa gratuita altamente generosa (hasta 15 RPM / 1M TPM).
  * Costos sumamente bajos en el plan de pago ($0.075 / millón de tokens de entrada).

---

## 2. Funcionalidades Principales

### A. Interacción Contextual de IA
Al seleccionar cualquier texto o frase en el visor de Okular, se habilitarán comandos rápidos de IA:
1. **Explicar:** Desglose didáctico del texto seleccionado.
2. **Traducir:** Traducción al idioma configurado manteniendo el contexto semántico.
3. **Buscar relacionado:** Encontrar fragmentos y conceptos similares en otros documentos de la biblioteca local.
4. **Contexto (Soporte Interno):** Búsqueda semántica dentro del *mismo documento* para encontrar y resaltar visualmente en Okular todas las secciones y párrafos adicionales que aporten información esencial para entender la frase seleccionada.

### B. Enfoque Pedagógico: Zona de Aprendizaje Próximo (ZDP)
* Por defecto, el asistente conversacional no entregará respuestas resueltas de inmediato.
* Actuará como un guía o tutor (técnica de *scaffolding* o andamiaje), formulando preguntas guías, relacionando conceptos previos y adaptando el nivel de asistencia según el conocimiento demostrado por el usuario.

### C. Visualización de la Biblioteca
El gestor de documentos contará con dos representaciones principales:
1. **Vista de Tabla:** Presentación detallada tradicional con columnas de metadatos (nombre, etiquetas, porcentaje de lectura, fecha, etc.).
2. **Vista de Grafo Semántico:** Mapa interactivo de nodos (documentos) y aristas (relación semántica basada en la cercanía de sus embeddings), facilitando la exploración visual y el descubrimiento de conexiones entre temas.

---

## 3. Flujo de Datos del Sistema

```mermaid
graph TD
    subgraph Frontend (Capa de Presentación - Fork de Okular)
        UI[Paneles React: Chat, Grafo y Tabla en QWebEngineView]
        Reader[Visor Nativo C++ de Okular / Anotaciones]
    end

    subgraph Backend / IPC (Capa de Control - FastAPI)
        Pipeline[Pipeline de Ingesta]
        Extract[Extractor de Texto]
        Chunk[Segmentador de Texto]
        Embed[Generador de Embeddings]
        DB[(Base de Datos Vectorial Local)]
    end

    subgraph Capa de IA (Modelos)
        LLM[Google Gemini API]
    end

    %% Ingesta de Documento
    PDF[Archivo PDF] --> Extract
    Extract --> Chunk
    Chunk --> Embed
    Embed --> DB

    %% Consulta de Chat
    UI -->|1. Pregunta/Acción del Usuario| Pipeline
    Pipeline -->|2. Búsqueda Vectorial| DB
    DB -->|3. Contexto Recuperado| Pipeline
    Pipeline -->|4. Prompt ZDP + Contexto| LLM
    LLM -->|5. Respuesta Didáctica| UI
    Pipeline -.->|6. Resaltar Citas/Contexto en Visor| Reader
```
