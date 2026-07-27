# Plan de Implementación: Spec 9 - Biblioteca: Tabla y Grafo

Este plan de desarrollo detalla los pasos concretos de codificación, instalación de dependencias y pruebas de integración para la Biblioteca digital (Tabla y Grafo).

---

## 1. Estrategia de Ejecución (Paso a Paso)

### Paso 1: Implementar Endpoint en FastAPI
1. **Modificar `/backend/app/api/v1/endpoints/library.py`:**
   - Importar `numpy` para promedios de vectores y cálculo de distancia.
   - Añadir el decorador `@router.get("/graph")`.
   - Obtener todos los documentos indexados de `VectorDB`.
   - Calcular para cada documento el vector medio de sus chunks.
   - Computar la matriz de similitud de coseno cruzada de todos los pares y retornar la estructura de `nodes` y `edges`.

### Paso 2: Modificar el Puente C++ (JSBridge)
1. **Modificar `/visor/src/jsbridge.h`:**
   - Añadir slots `openDocumentFromReact(const QString &filePath)` y `setCurrentTab(int tabIndex)`.
   - Añadir señales `openDocumentRequested(const QString &filePath)` y `currentTabChangeRequested(int tabIndex)`.
2. **Modificar `/visor/src/jsbridge.cpp`:**
   - Implementar `openDocumentFromReact` emitiendo la señal `openDocumentRequested`.
   - Implementar `setCurrentTab` emitiendo la señal `currentTabChangeRequested`.

### Paso 3: Modificar MainWindow C++
1. **Modificar `/visor/src/mainwindow.h`:**
   - Declarar el slot `setCurrentTab(int tabIndex)`.
2. **Modificar `/visor/src/mainwindow.cpp`:**
   - Conectar `m_bridge->openDocumentRequested` a `MainWindow::openDocument`.
   - Conectar `m_bridge->currentTabChangeRequested` a `MainWindow::setCurrentTab`.
   - Implementar `MainWindow::setCurrentTab` para llamar a `m_tabWidget->setCurrentIndex(tabIndex)`.

### Paso 4: Declarar Interfaces en TypeScript
1. **Modificar `/frontend/src/qwebchannel.ts`:**
   - Declarar métodos `openDocumentFromReact: (filePath: string) => Promise<void>` y `setCurrentTab: (tabIndex: number) => Promise<void>` en la interfaz `qtBridge`.

### Paso 5: Instalar Dependencias de Grafo
1. **Instalar Cytoscape en el frontend:**
   - Ejecutar `npm install cytoscape` y `npm install @types/cytoscape --save-dev` en la carpeta `frontend/`.

### Paso 6: Crear el Componente de Grafo en React
1. **Crear `/frontend/src/components/LibraryGraph.tsx`:**
   - Iniciar Cytoscape sobre un contenedor `cy-container` usando `useEffect`.
   - Recibir propiedades `nodes`, `edges` y `threshold` (umbral de similitud).
   - Recibir callbacks `onSelectNode` para informar al componente padre del nodo seleccionado.
   - Refrescar dinámicamente las aristas en Cytoscape cada vez que cambie `threshold`.

### Paso 7: Actualizar App.tsx y el Diseño CSS
1. **Modificar `/frontend/src/App.tsx`:**
   - Reemplazar la maqueta de biblioteca en `renderLibrary()` por la interfaz real dividida.
   - Consultar `GET /api/v1/library/graph` y `GET /api/v1/documents` al montar.
   - Mostrar el buscador superior, selector de tags y la tabla con barra de progreso y acciones (Play para abrir, Trash para eliminar).
   - Integrar `<LibraryGraph>` con un control de slider para el umbral de similitud.
2. **Modificar `/frontend/src/index.css`:**
   - Añadir estilos estéticos para el grafo Cytoscape, el slider, el layout de la biblioteca y el panel de detalles del documento seleccionado.

---

## 2. Plan de Asignación y Paralelización
La implementación será realizada de forma secuencial por el agente principal para garantizar la consistencia en el cálculo de vectores y la sincronía de los slots de C++ con el frontend React.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Con la aprobación de este plan de desarrollo:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Procederemos a realizar las modificaciones e integraciones del visor y de React.
