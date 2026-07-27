# Formulario de Requisitos: Spec 8 - Interfaz de Chat y Referencias

Este formulario tiene como objetivo definir el alcance, comportamiento y decisiones de diseño para la **Spec 8: Interfaz de Chat y Referencias**, que conectará el panel de chat en React con el backend de FastAPI e interactuará con el visor C++ para la visualización de referencias y citas.

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para poder proceder a la sesión de refinamiento y diseño de la arquitectura.

---

## 1. Comportamiento de Ingesta desde el Visor

Cuando abres un PDF local en el visor (C++), puede estar ya indexado en la base de datos o no.

* **1.1. ¿Cómo debería comportarse el sistema si el documento abierto no está indexado en la base de datos?**
  - [x] **Flujo guiado (Recomendado):** La interfaz de React detecta que no está indexado y muestra una pantalla intermedia con un botón *"Procesar Documento"*. Al hacer clic, C++ sube o procesa el archivo local mediante la API de FastAPI e informa a React del progreso antes de habilitar el chat.
  - [ ] **Ingesta silenciosa:** Tan pronto como C++ detecta que no está indexado, inicia la ingesta en segundo plano automáticamente sin pedir confirmación.
  - [ ] **Manual por el usuario:** El usuario debe ir a la pestaña "Biblioteca" e importar el archivo manualmente allí primero.

---

## 2. Visualización e Interacción de Citas Bibliográficas

El backend extrae y devuelve citas en corchetes `[1]`, `[2]`, etc.

* **2.1. Al hacer clic en una cita (ej. `[3]`) en los mensajes de respuesta de la IA en el chat, ¿qué acción prefieres que realice la aplicación?**
  - [ ] **Acción A (Solo Tooltip):** Mostrar un popover/tooltip interactivo sobre la cita con el detalle de la entrada bibliográfica (extraída de los metadatos globales del documento).
  - [ ] **Acción B (Navegación en el PDF):** Hacer que el visor C++ salte inmediatamente a la página de la sección "References/Bibliografía" del documento.
  - [x] **Acción Híbrida (Recomendado):** Mostrar el tooltip con la entrada detallada Y añadir un botón *"Ir a la referencia en el PDF"* que envíe el comando a C++ para desplazar el visor.

---

## 3. Renderizado de Mensajes de IA

La IA responde utilizando formato Markdown y andamiaje pedagógico (ZDP).

* **3.1. ¿Qué librería de React prefieres utilizar para el formateo estético de Markdown?**
  - [x] `react-markdown` (Estándar, permite customizar elementos como listas, código y bloques fácilmente).
  - [ ] Crear un formateador simple propio en expresiones regulares (Evita añadir dependencias NPM extra).
  - [ ] Otra (especificar): 

* **3.2. ¿Deberíamos habilitar respuestas en tiempo real (Streaming / Server-Sent Events) en la interfaz de chat?**
  - [x] Sí (Recomendado para una experiencia de IA moderna y fluida).
  - [ ] No (Respuestas estáticas de golpe tras terminar la llamada de API).

---

## 4. Gestión del Historial de Chat

* **4.1. ¿Qué opciones de gestión del historial de chat conversacional deberíamos incluir en el panel lateral?**
  - [x] Botón de *"Limpiar Historial"* en la cabecera del chat (Borra los mensajes de la base de datos local para el documento actual).
  - [x] Auto-scroll al final del chat al recibir nuevos tokens en streaming.
  - [ ] Botón para exportar el chat a formato Markdown/TXT.

---

## 5. Alcance Inicial (In-Scope vs. Out-of-Scope)

* **In-Scope (Qué hace):**
  - Consumo del endpoint de chat en streaming (`POST /api/v1/chat/message`) mediante `EventSource` o peticiones `fetch` asíncronas para lectura de chunks.
  - Recuperación y renderizado del historial del chat (`GET /api/v1/chat/history/{document_id}`) al cargar el documento.
  - Botón de limpieza de chat (`DELETE /api/v1/chat/history/{document_id}`).
  - Cálculo del hash SHA-256 en C++ al abrir el archivo PDF para obtener el `document_id` real.
  - Flujo de comunicación IPC para reportar el estado de ingesta de un PDF no indexado.
  - Renderizado premium de burbujas de chat, Markdown, código fuente y citas cliqueables.
  
* **Out-of-Scope (Qué NO hace en esta fase):**
  - La visualización de la biblioteca y el grafo semántico (Spec 9).
  - Los atajos del teclado en C++ para capturar texto seleccionado del PDF y enviarlo a las acciones rápidas (Spec 10).
