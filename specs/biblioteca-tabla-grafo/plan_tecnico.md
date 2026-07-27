# Plan Técnico: Spec 9 - Biblioteca: Tabla y Grafo

Este plan técnico detalla los cambios en el backend de FastAPI para calcular la similitud semántica de documentos, los slots de control en C++, y el diseño del panel de biblioteca con Cytoscape.js en React.

---

## 1. Archivos Impactados

### A. Backend FastAPI
```text
backend/app/api/v1/endpoints/
└── library.py                  # Modificar: Añadir endpoint GET /graph
```

### B. Subproyecto C++ (Visor)
```text
visor/src/
├── jsbridge.h                  # Modificar: Añadir slots openDocumentFromReact y setCurrentTab
├── jsbridge.cpp                # Modificar: Implementar slots emitiendo señales internas
├── mainwindow.h                # Modificar: Declarar el slot setCurrentTab
└── mainwindow.cpp              # Modificar: Conectar señales y cambiar de pestaña activa
```

### C. React Frontend
```text
frontend/src/
├── qwebchannel.ts              # Modificar: Declarar tipos de los nuevos métodos
├── App.tsx                     # Modificar: Implementar la vista renderLibrary con tabla y panel
└── components/
    └── LibraryGraph.tsx        # Crear: Componente interactivo de Cytoscape.js con filtro de umbral
```

---

## 2. Detalle de los Cambios en el Backend

Implementaremos el endpoint `GET /api/v1/library/graph` en `library.py`:
1. Recuperar todos los documentos de la base de datos.
2. Para cada documento, recuperar todos sus chunks y promediar sus vectores de embedding (2048 dimensiones) para generar el "vector representativo del documento".
3. Calcular la similitud de coseno para todos los pares de documentos:
   $$\text{similitud} = \frac{A \cdot B}{\|A\| \|B\|}$$
4. Retornar los nodos (metadatos del documento) y aristas (relaciones que tengan una similitud $\ge 0.3$).

```python
import numpy as np

@router.get("/graph")
def get_library_graph():
    docs = VectorDB.get_documents()
    if not docs:
        return {"nodes": [], "edges": []}
        
    doc_vectors = {}
    nodes = []
    
    for doc in docs:
        doc_id = doc["document_id"]
        chunks = VectorDB.get_document_chunks(doc_id)
        if chunks:
            # Promediar embeddings
            vectors = [np.array(c["vector"]) for c in chunks if "vector" in c]
            if vectors:
                doc_vectors[doc_id] = np.mean(vectors, axis=0)
                nodes.append({
                    "id": doc_id,
                    "label": doc["filename"],
                    "pages_count": doc["pages_count"],
                    "reading_progress": doc.get("reading_progress", 0.0),
                    "added_at": doc["added_at"],
                    "file_path": chunks[0].get("file_path", "")  # ruta física
                })
                
    # Calcular similitud coseno cruzada
    edges = []
    doc_ids = list(doc_vectors.keys())
    for i in range(len(doc_ids)):
        for j in range(i + 1, len(doc_ids)):
            id_a, id_b = doc_ids[i], doc_ids[j]
            vec_a, vec_b = doc_vectors[id_a], doc_vectors[id_b]
            
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)
            if norm_a > 0 and norm_b > 0:
                sim = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
                # Guardar aristas con similitud significativa
                if sim >= 0.4:
                    edges.append({
                        "source": id_a,
                        "target": id_b,
                        "similarity": sim
                    })
                    
    return {"nodes": nodes, "edges": edges}
```

---

## 3. Detalle de los Slots C++ (IPC)

* **En `jsbridge.h`:**
```cpp
public slots:
    void openDocumentFromReact(const QString &filePath);
    void setCurrentTab(int tabIndex);

signals:
    void openDocumentRequested(const QString &filePath);
    void currentTabChangeRequested(int tabIndex);
```

* **En `mainwindow.cpp`:**
```cpp
// Conectar en setupVisor()
connect(m_bridge, &JSBridge::openDocumentRequested, this, &MainWindow::openDocument);
connect(m_bridge, &JSBridge::currentTabChangeRequested, this, &MainWindow::setCurrentTab);

void MainWindow::setCurrentTab(int tabIndex)
{
    if (m_tabWidget && tabIndex >= 0 && tabIndex < m_tabWidget->count()) {
        m_tabWidget->setCurrentIndex(tabIndex);
    }
}
```

---

## 4. Detalle del Frontend React

### A. Componente de Grafo (`LibraryGraph.tsx`)
* Instalaremos `cytoscape` para la renderización interactiva en un elemento `<div id="cy-container">`.
* Utilizaremos un slider de HTML en el panel superior para regular el umbral de filtrado:
```typescript
const filteredEdges = edges.filter(e => e.similarity >= threshold);
```
* Cytoscape actualizará el dataset dinámicamente y aplicará un layout tipo `cose` (fuerzas concéntricas) para reordenar las posiciones de forma fluida.

### B. Tabla de Biblioteca y Diseño Dividido (`App.tsx`)
La vista Biblioteca a pantalla completa tendrá dos columnas (Grid 45% / 55%):
1. **Izquierda (Tabla):**
   * Buscador textual que filtre nombres de archivo.
   * Filtro por tags en un selector superior.
   * Listado de documentos en filas con barra de progreso circular o lineal, y botones de acción (Play para abrir, Trash para eliminar).
2. **Derecha (Grafo):**
   * El visor de Cytoscape centrado con los controles de zoom y el slider del umbral.
   * Un panel inferior que revele detalles al seleccionar un documento (Nombre, número de páginas, tags, y botón para cargarlo directamente).

---

## 5. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación del plan técnico:
1. Realizaremos un **commit en git** con el plan técnico aprobado.
2. Escribiremos el **Plan de Implementación** detallando los comandos y cambios a realizar.
