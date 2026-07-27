# Especificación de Requisitos (Spec): Spec 9 - Biblioteca: Tabla y Grafo

Este documento define la especificación de diseño y comportamiento para la **Spec 9: Biblioteca: Tabla y Grafo**, en la Pestaña 2 a pantalla completa del lector de PDF.

---

## 1. Definición del Problema y Objetivos
El lector digital integrado necesita una vista centralizada donde el usuario pueda:
1. Gestionar su biblioteca de documentos PDFs indexados (búsqueda, filtros por tags, ordenamiento, y progreso de lectura).
2. Ver visualmente las interconexiones temáticas entre sus papers/libros (mediante un Grafo de Similitud Semántica).
3. Abrir o reanudar chats de documentos con un solo clic, permitiendo que la interfaz de biblioteca interactúe con el visor nativo C++ (abriendo el archivo y activando la pestaña del lector).

---

## 2. Alcance (Límites del Sistema)

### Qué HACE la Spec (In-Scope)
* **Backend de FastAPI (API de Grafo):**
  - Implementación del endpoint `GET /api/v1/library/graph` que recupere todos los documentos de LanceDB.
  - Para cada documento, calcular su "embedding de documento" promediando los vectores de todos sus chunks.
  - Calcular la similitud de coseno entre todos los pares de documentos.
  - Devolver una lista de nodos (documentos con sus metadatos) y aristas (relaciones de similitud con pesos `0.0 - 1.0`).
* **Frontend React (Tabla de Biblioteca):**
  - Tabla interactiva con búsqueda textual sobre el título/nombre de archivo.
  - Paginación y ordenación por fecha de adición, progreso y nombre.
  - Filtros y visualización por badges de etiquetas (tags).
  - Acciones: *"Abrir en Visor"* y *"Eliminar Documento"*.
* **Frontend React (Grafo Semántico):**
  - Visualización del grafo interactivo 2D utilizando `cytoscape.js`.
  - Slider para ajustar interactivamente el "Umbral de Similitud" mínimo (aristas con peso inferior al umbral se ocultan dinámicamente).
  - Al hacer clic en un nodo, mostrar un panel de detalles rápidos del documento y la opción de abrirlo.
* **Integración IPC C++:**
  - El puente `JSBridge` expone slots para:
    - `void openDocumentFromReact(const QString &filePath)`: Carga el PDF indicado.
    - `void setCurrentTab(int tabIndex)`: Permite cambiar a la pestaña 1 (Visor/Chat) o pestaña 2 (Biblioteca) de forma programática.

### Qué NO HACE la Spec (Out-of-Scope)
* **No implementa renderizado 3D para el grafo.**
* **No realiza indexación en lote (se mantiene la ingesta unitaria).**

---

## 3. Arquitectura y Flujos de Datos

### Flujo de Navegación de Documento desde React
```mermaid
sequenceDiagram
    participant React as Biblioteca React (Pest. 2)
    participant C++ as Visor C++ (Okular)
    participant API as FastAPI Backend

    React->>C++: openDocumentFromReact(filePath) (Slot IPC)
    C++->>C++: openDocument(filePath) -> Carga en Okular KPart
    C++->>React: fileLoaded(filePath, documentId) (Emitir señal)
    React->>C++: setCurrentTab(0) (Slot IPC - cambia a pestaña Lector)
    C++->>C++: m_tabWidget->setCurrentIndex(0)
    React->>React: Recibe fileLoaded, carga ChatPanel en Pest. 1
```

### Formato de Respuesta del Endpoint `GET /api/v1/library/graph`
```json
{
  "nodes": [
    {
      "id": "hash_sha256_1",
      "label": "attention_paper.pdf",
      "pages_count": 15,
      "reading_progress": 0.35,
      "added_at": "2026-07-26T20:00:00"
    }
  ],
  "edges": [
    {
      "source": "hash_sha256_1",
      "target": "hash_sha256_2",
      "similarity": 0.84
    }
  ]
}
```

---

## 4. Próxima Fase (Fase 2: Planificación Técnica)
Con la aprobación de esta especificación:
1. Realizaremos un **commit en git** con la especificación formal aprobada.
2. Escribiremos el **Plan Técnico** detallando dependencias, el cálculo matemático de similitud de coseno en FastAPI, los slots en `MainWindow` e `JSBridge`, y la integración con Cytoscape en React.
