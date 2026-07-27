# Especificación de Requisitos (Spec): Spec 10 - Atajos de Selección del Visor

Este documento define la especificación de diseño y comportamiento para la **Spec 10: Atajos de Selección del Visor** utilizando la metodología Spec Driven Development (SDD).

---

## 1. Definición del Problema y Objetivos
Para maximizar la productividad y fluidez en la lectura de papers científicos, el usuario necesita disparar acciones rápidas de IA (explicar o resumir) sobre términos o párrafos seleccionados del PDF utilizando combinaciones de teclas, sin tener que copiar, pegar y redactar manualmente en el chat.

---

## 2. Alcance (Límites del Sistema)

### Qué HACE la Spec (In-Scope)
* **Atajos de Teclado (C++):**
  - Registro de tres atajos clave en `MainWindow`:
    - `Alt+E`: Dispara la acción *"Explicar"* sobre la selección.
    - `Alt+R`: Dispara la acción *"Resumir"* sobre la selección.
    - `Alt+T`: Copia la selección a la caja de entrada de chat.
* **Captura de Selección (Okular KPart & Portapapeles):**
  - Al presionar el atajo, C++ obtiene el widget del KPart y ejecuta programáticamente la acción de copia nativa de Okular (`edit_copy`) para colocar la selección en el portapapeles.
  - C++ lee el texto resultante desde `QClipboard`.
  - Si el texto está vacío, muestra un mensaje informativo en el `statusBar()` de `MainWindow` y detiene la ejecución.
* **Señalización IPC (`JSBridge`):**
  - Definición y emisión de la señal `void textSelectedForAction(const QString &text, const QString &actionType)` a través del WebChannel.
* **Acciones en React:**
  - React escucha la señal `textSelectedForAction`.
  - Si `actionType` es `"explain"`: envía automáticamente el mensaje *"Explícame el siguiente fragmento: [texto]"* e inicia la respuesta en streaming.
  - Si `actionType` es `"summarize"`: envía automáticamente *"Resume el siguiente fragmento: [texto]"* e inicia la respuesta en streaming.
  - Si `actionType` es `"ask"`: pre-llena la caja de texto del input con el texto seleccionado, coloca el foco en el input y no envía nada, permitiendo al usuario redactar.

### Qué NO HACE la Spec (Out-of-Scope)
* **No implementa atajos de teclado globales fuera de la ventana activa de la aplicación.**

---

## 3. Arquitectura y Flujos de Datos

### Flujo de Captura de Texto y Acción Rápida
```mermaid
sequenceDiagram
    participant Usuario as Usuario
    participant C++ as Visor C++ (MainWindow)
    participant Bridge as JSBridge (IPC)
    participant React as Chat React

    Usuario->>C++: Presiona Alt+E (sobre texto seleccionado)
    C++->>C++: Dispara edit_copy de Okular KPart
    C++->>C++: Lee QClipboard::text()
    alt Selección vacía
        C++-->>Usuario: Muestra en statusbar "Selecciona texto..."
    else Selección con texto
        C++->>Bridge: textSelectedForAction(text, "explain")
        Bridge->>React: textSelectedForAction(text, "explain")
        React->>React: Inserta y envía mensaje al chat
        React->>React: Inicia streaming SSE de respuesta
    end
```

---

## 4. Próxima Fase (Fase 2: Planificación Técnica)
Con la aprobación de esta especificación:
1. Realizaremos un **commit en git** con la especificación formal aprobada.
2. Escribiremos el **Plan Técnico** detallando la inicialización de atajos en QAction, la obtención de la acción de copia en Okular KPart y la lógica de autorepuesta en React.
