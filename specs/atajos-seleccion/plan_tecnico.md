# Plan Técnico: Spec 10 - Atajos de Selección del Visor

Este plan técnico detalla el registro de atajos de teclado en C++, la obtención de la selección desde Okular, la transferencia asíncrona por el puente y el consumo interactivo en React.

---

## 1. Archivos Impactados

### A. Subproyecto C++ (Visor)
```text
visor/src/
├── jsbridge.h                  # Modificar: Declarar la señal textSelectedForAction
├── mainwindow.h                # Modificar: Declarar métodos para atajos y slots de atajos
└── mainwindow.cpp              # Modificar: Registrar Alt+E/R/T y capturar selección de Okular
```

### B. React Frontend
```text
frontend/src/
├── qwebchannel.ts              # Modificar: Declarar la nueva señal en el puente qtBridge
└── components/
    └── ChatPanel.tsx           # Modificar: Suscribirse a la señal de atajo y disparar acciones
```

---

## 2. Detalle de los Cambios C++

### A. Puente IPC (`jsbridge.h`)
Agregamos la firma de la señal que transmitirá el texto seleccionado a React:
```cpp
signals:
    // ...
    void textSelectedForAction(const QString &text, const QString &actionType);
```

### B. Registro y Captura de Atajos (`mainwindow.h` / `mainwindow.cpp`)
* En `mainwindow.h`, declaramos:
```cpp
private:
    void setupShortcuts();
    void handleShortcutTriggered(const QString &actionType);
```

* En `mainwindow.cpp`, implementamos el registro de atajos en `setupShortcuts()` (se llama al final del constructor o en `setupVisor`):
```cpp
void MainWindow::setupShortcuts()
{
    // Alt+E: Explicar
    QAction *explainAction = new QAction(this);
    explainAction->setShortcut(QKeySequence(Qt::ALT | Qt::Key_E));
    connect(explainAction, &QAction::triggered, this, [this]() {
        handleShortcutTriggered(QStringLiteral("explain"));
    });
    addAction(explainAction);

    // Alt+R: Resumir
    QAction *summarizeAction = new QAction(this);
    summarizeAction->setShortcut(QKeySequence(Qt::ALT | Qt::Key_R));
    connect(summarizeAction, &QAction::triggered, this, [this]() {
        handleShortcutTriggered(QStringLiteral("summarize"));
    });
    addAction(summarizeAction);

    // Alt+T: Copiar al Prompt
    QAction *askAction = new QAction(this);
    askAction->setShortcut(QKeySequence(Qt::ALT | Qt::Key_T));
    connect(askAction, &QAction::triggered, this, [this]() {
        handleShortcutTriggered(QStringLiteral("ask"));
    });
    addAction(askAction);
}
```

* En `handleShortcutTriggered()`, extraemos la selección utilizando el portapapeles y notificamos a React:
```cpp
#include <QClipboard>
#include <QGuiApplication>

void MainWindow::handleShortcutTriggered(const QString &actionType)
{
    if (!m_part) return;

    // Ejecutar la acción de copiar nativa de Okular KPart
    QAction *okularCopy = m_part->action(QStringLiteral("edit_copy"));
    if (okularCopy) {
        okularCopy->trigger();
    }

    // Recuperar texto del portapapeles
    QString text = QGuiApplication::clipboard()->text().trimmed();

    if (text.isEmpty()) {
        statusBar()->showMessage(tr("Selecciona texto en el PDF primero."), 3000);
        return;
    }

    qInfo() << "IPC: Enviando selección de texto para atajo:" << actionType;
    emit m_bridge->textSelectedForAction(text, actionType);
}
```

---

## 3. Detalle de los Cambios React

### A. Tipado TypeScript (`qwebchannel.ts`)
Añadimos la señal en las declaraciones del canal:
```typescript
      textSelectedForAction: {
        connect: (callback: (text: string, actionType: string) => void) => void;
        disconnect: (callback: (text: string, actionType: string) => void) => void;
      };
```

### B. Consumo y Autorespuesta (`ChatPanel.tsx`)
1. Nos suscribimos a `textSelectedForAction` en un `useEffect` dependiente de `documentId`.
2. Para `"explain"` y `"summarize"`, llamamos a una función interna de envío directo que inserta el texto pre-formateado y envía la consulta por streaming a FastAPI.
3. Para `"ask"`, pre-llenamos el input del chat con el texto y le damos foco al elemento input.

---

## 4. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación del plan técnico:
1. Realizaremos un **commit en git** con el plan técnico aprobado.
2. Escribiremos el **Plan de Implementación** detallando los comandos y cambios a realizar.
