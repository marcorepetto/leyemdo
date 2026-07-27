# Formulario de Requisitos: Spec 10 - Atajos de Selección del Visor

Este formulario tiene como objetivo definir el comportamiento de los atajos del teclado en C++ para capturar texto seleccionado del PDF e interactuar con el panel de chat en React.

---

## 1. Asignación de Atajos del Teclado

* **1.1. ¿Qué combinaciones de teclas prefieres para disparar las acciones contextuales rápidas sobre el texto seleccionado?**
  - [x] **Opción A (Recomendada - Alt+Teclas):**
    - `Alt+E`: **Explicar término/párrafo** (Envía la selección al chat pidiendo una explicación didáctica).
    - `Alt+R`: **Resumir selección** (Envía la selección al chat solicitando un resumen estructurado).
    - `Alt+T`: **Preguntar al Tutor** (Copia el texto al campo de entrada de chat para que el usuario redacte su pregunta).
  - [ ] **Opción B (Ctrl+Teclas):**
    - `Ctrl+Shift+E`: Explicar.
    - `Ctrl+Shift+R`: Resumir.
    - `Ctrl+Shift+T`: Enviar al prompt.

---

## 2. Comportamiento en la Interfaz de Chat (React)

* **2.1. Al disparar "Explicar" (`Alt+E`) o "Resumir" (`Alt+R`), ¿cómo debe responder la barra de chat?**
  - [x] **Envío automático (Recomendado):** Envía la pregunta al backend e inicia la respuesta en streaming de inmediato, ahorrándole clics al usuario.
  - [ ] **Pre-llenado:** Solo escribe la pregunta en la caja de texto y deja que el usuario presione "Enviar" manualmente.

---

## 3. Manejo de Errores y Comportamiento cuando no hay Selección

* **3.1. Si el usuario presiona un atajo pero no tiene texto seleccionado en el PDF, ¿qué debe hacer la aplicación?**
  - [x] Mostrar un mensaje en la barra de estado inferior: *"Selecciona texto en el PDF primero."* y no hacer nada.
  - [ ] Utilizar el texto completo de la página actual como contexto por defecto.

---

## 4. Alcance (In-Scope vs. Out-of-Scope)

* **In-Scope:**
  - Creación de acciones de teclado (`QAction`) en `MainWindow` vinculadas a los atajos de teclado correspondientes.
  - Interceptación y disparo de la acción nativa de copia de Okular KPart (`edit_copy`) para colocar el texto seleccionado en el portapapeles.
  - Lectura asíncrona del portapapeles (`QClipboard`) desde C++.
  - Envío del texto seleccionado a React mediante la señal `textSelectedForAction(text, actionType)` en `JSBridge`.
  - Escucha de la señal en React, auto-envío de mensajes y pre-llenado de la caja de texto según el tipo de acción.
  
* **Out-of-Scope:**
  - Soporte de atajos fuera de la ventana del visor (atajos globales del sistema operativo).
