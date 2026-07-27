# Formulario de Requisitos: Spec 9 - Biblioteca: Tabla y Grafo

Este formulario tiene como objetivo definir el alcance, comportamiento y decisiones de diseño para la **Spec 9: Biblioteca: Tabla y Grafo**, que constituirá la vista a pantalla completa del sistema de lectura digital en la Pestaña 2 del visor.

---

## 1. Columnas y Acciones de la Tabla de Documentos

La tabla interactiva mostrará todos los archivos PDFs indexados.

* **1.1. ¿Qué columnas e interacciones prefieres incluir en la tabla?**
  - [x] **Columnas básicas:** Nombre de archivo, Cantidad de páginas, Caracteres totales, Fecha de adición.
  - [x] **Barra de Progreso:** Visualización del progreso de lectura (0% - 100%) y posibilidad de actualizarlo/marcarlo como completado.
  - [x] **Tags/Etiquetas:** Visualizar los tags del documento con posibilidad de filtrarlos.
  - [x] **Acciones directas:** Botón *"Abrir en Visor"* (envía comando IPC a C++ para abrir el PDF y cambiar a la pestaña 1), Botón *"Chatear"* (cambia a la pestaña 1 con el chat de ese archivo abierto), y Botón *"Eliminar"* (remueve de la base de datos).

---

## 2. Visualización del Grafo Semántico

El grafo conectará los documentos basándose en su similitud temática/semántica (calculada a partir de los embeddings de sus chunks).

* **2.1. ¿Qué librería de visualización prefieres utilizar para el grafo interactivo?**
  - [x] **Cytoscape.js (Recomendado):** Muy ligera, excelente soporte para layouts de fuerza y eventos táctiles/click directos.
  - [ ] **D3.js pura:** Mayor flexibilidad de personalización SVG, pero requiere más configuración manual en React.
  - [ ] **react-force-graph:** Excelente renderizado 2D/Canvas y simulaciones de fuerza fluidas.

* **2.2. ¿Cómo se determinará si dos documentos están conectados en el grafo?**
  - [x] **Umbral dinámico (Recomendado):** El backend calcula la matriz de similitud de coseno entre todos los documentos. El frontend muestra un slider de "Umbral de Similitud" (ej: de 0.5 a 1.0) para que el usuario filtre interactivamente las conexiones débiles o fuertes en tiempo real.
  - [ ] **Umbral fijo:** Las conexiones se calculan en el backend con un umbral fijo (ej: >0.7) y no se pueden alterar en el frontend.

---

## 3. Comportamiento de Integración C++ (Navegación e IPC)

* **3.1. Cuando el usuario hace clic en *"Abrir en Visor"* o hace doble clic en un nodo del grafo, ¿qué comportamiento esperas en la app nativa?**
  - [x] El visor C++ carga el archivo PDF indicado en el KPart, actualiza el chat en la pestaña 1, y cambia la pestaña activa del `QTabWidget` de la pestaña 2 (Biblioteca) a la pestaña 1 (Visor/Chat).
  - [ ] Carga el PDF en segundo plano pero se mantiene en la pestaña 2 de biblioteca hasta que el usuario cambie de pestaña manualmente.

---

## 4. Alcance (In-Scope vs. Out-of-Scope)

* **In-Scope:**
  - Nuevo endpoint en FastAPI `GET /api/v1/library/graph` que calcule similitudes coseno y devuelva la estructura de nodos/aristas.
  - Renderizado en React (Pestaña 2) de un layout dividido: lado izquierdo con la Tabla de documentos, lado derecho con el Grafo interactivo.
  - Búsqueda, paginación, filtros de tags y ordenación en la tabla.
  - Slots en `JSBridge` para abrir archivos locales (`openDocumentFromReact`) y cambiar de pestaña activa (`setCurrentTab`).
  
* **Out-of-Scope:**
  - Indexación de formatos que no sean PDF.
  - Visualización en 3D del grafo conceptual (se mantiene en 2D interactivo).
