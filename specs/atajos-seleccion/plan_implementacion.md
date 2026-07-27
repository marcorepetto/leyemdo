# Plan de Implementación: Spec 10 - Atajos de Selección del Visor

Este plan detalla la estrategia de codificación paso a paso para capturar texto seleccionado del PDF mediante atajos de teclado e interactuar con el chat de IA en React.

---

## 1. Estrategia de Ejecución (Paso a Paso)

### Paso 1: Extender la Señal en JSBridge
1. **Modificar `/visor/src/jsbridge.h`:**
   - Declarar la señal `void textSelectedForAction(const QString &text, const QString &actionType)`.

### Paso 2: Declarar Métodos de Atajos en MainWindow
1. **Modificar `/visor/src/mainwindow.h`:**
   - Declarar el método privado `void setupShortcuts()`.
   - Declarar el slot privado `void handleShortcutTriggered(const QString &actionType)`.

### Paso 3: Registrar Atajos y Extraer Selección en MainWindow
1. **Modificar `/visor/src/mainwindow.cpp`:**
   - Llamar a `setupShortcuts()` al final del constructor o en `setupVisor()`.
   - Implementar `setupShortcuts()` registrando tres `QAction` para `Alt+E` ("explain"), `Alt+R` ("summarize") y `Alt+T` ("ask") asociadas a la ventana.
   - Implementar `handleShortcutTriggered(actionType)`:
     - Disparar la acción nativa de Okular `m_part->action("edit_copy")->trigger()`.
     - Leer el portapapeles con `QGuiApplication::clipboard()->text().trimmed()`.
     - Si está vacío, mostrar advertencia en el `statusBar()`.
     - Si tiene contenido, emitir la señal `m_bridge->textSelectedForAction(text, actionType)`.

### Paso 4: Actualizar Interfaces TypeScript
1. **Modificar `/frontend/src/qwebchannel.ts`:**
   - Añadir la señal `textSelectedForAction` al tipado del objeto `qtBridge`.

### Paso 5: Escuchar e Interactuar en ChatPanel React
1. **Modificar `/frontend/src/components/ChatPanel.tsx`:**
   - Definir una función auxiliar para realizar el envío directo de consultas contextuales (ej: `submitShortcutQuestion(prompt)`).
   - En un `useEffect` que se active al cambiar de `documentId`, suscribirse a `window.qtBridge.textSelectedForAction`:
     - Si la acción es `"explain"`, disparar la consulta de explicación del fragmento.
     - Si es `"summarize"`, disparar la consulta de resumen del fragmento.
     - Si es `"ask"`, colocar el texto seleccionado en el input de chat y darle el foco.
   - Asegurar la desconexión del callback al desmontarse.

### Paso 6: Compilación y Pruebas
1. Compilar el visor C++.
2. Asegurar que el backend y frontend estén activos.
3. Abrir un documento indexado en el visor.
4. Seleccionar un párrafo o concepto del PDF y probar los tres atajos (`Alt+E`, `Alt+R`, `Alt+T`), verificando las respuestas automáticas e inputs llenados de manera interactiva.

---

## 2. Plan de Asignación y Paralelización
La tarea será completada en solitario por el agente principal para garantizar la correcta secuenciación de los slots y señales en C++ y React.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Con la aprobación de este plan:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Procederemos a realizar las modificaciones e integraciones del visor y de React.
