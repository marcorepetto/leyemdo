# Plan Técnico: Spec 7 - Entorno de Integración Web

Este plan técnico detalla los archivos a crear y modificar, la arquitectura del puente de comunicación IPC (C++/JS) y el diseño de la interfaz de usuario en pestañas con QSplitter.

---

## 1. Archivos Impactados

### A. Subproyecto Visor C++ (Modificaciones y Creaciones)
```text
visor/
├── CMakeLists.txt              # Modificar: Buscar y enlazar Qt6::WebEngineWidgets y Qt6::WebChannel
└── src/
    ├── main.cpp                # Modificar: Permitir pasar banderas de depuración de WebEngine
    ├── mainwindow.h            # Modificar: Cambiar el layout central a QTabWidget y splitter
    ├── mainwindow.cpp          # Modificar: Configurar QSplitter, QWebEngineView y QWebChannel
    ├── jsbridge.h              # Crear: Clase QObject expuesta a JS
    └── jsbridge.cpp            # Crear: Lógica de comunicación IPC
```

### B. Subproyecto React Frontend (Creación en `/frontend/`)
```text
frontend/
├── package.json                # Crear: Configuración de NPM y scripts de Vite
├── vite.config.ts              # Crear: Configuración del servidor de desarrollo de Vite
├── index.html                  # Crear: Plantilla HTML principal
├── src/
│   ├── main.tsx                # Crear: Entrada de renderizado de React
│   ├── App.tsx                 # Crear: Componente principal con enrutamiento simple
│   └── qwebchannel.ts          # Crear: Implementación adaptada de qwebchannel.js en TypeScript
└── tsconfig.json               # Crear: Configuración de TypeScript
```

---

## 2. Detalle de los Cambios C++

### A. CMakeLists.txt
Añadiremos los módulos `WebEngineWidgets` y `WebChannel` al sistema de compilación:
```cmake
# Buscar Dependencias
find_package(Qt6 COMPONENTS Widgets Core WebEngineWidgets WebChannel REQUIRED)
find_package(KF6Parts REQUIRED)
find_package(KF6XmlGui REQUIRED)
find_package(KF6I18n REQUIRED)
find_package(KF6CoreAddons REQUIRED)
find_package(Okular::Core REQUIRED)

# Enlazar Bibliotecas
target_link_libraries(lector-visor
    PRIVATE
    Qt6::Widgets
    Qt6::Core
    Qt6::WebEngineWidgets
    Qt6::WebChannel
    KF6::Parts
    KF6::XmlGui
    KF6::I18n
    KF6::CoreAddons
    Okular::Core
)
```

### B. Clase JSBridge (`jsbridge.h` y `jsbridge.cpp`)
Esta clase heredará de `QObject` y será registrada en el `QWebChannel`.
```cpp
#pragma once
#include <QObject>

class JSBridge : public QObject
{
    Q_OBJECT

public:
    explicit JSBridge(QObject *parent = nullptr);

public slots:
    // Slot invocado desde JavaScript
    void postMessage(const QString &message);

signals:
    // Señal emitida a C++ cuando llega un mensaje de JS
    void messageReceived(const QString &message);
    
    // Señal enviada a JS cuando se abre un PDF en C++
    void fileLoaded(const QString &filePath);
};
```

### C. Rediseño de MainWindow (`mainwindow.cpp`)
El layout se estructurará de la siguiente forma:
1. Reemplazar el widget central con un `QTabWidget`.
2. **Pestaña 1 (Documento):**
   - Contiene un `QSplitter` horizontal.
   - Panel izquierdo: Widget del KPart de Okular.
   - Panel derecho: `QWebEngineView` que carga `/chat`.
3. **Pestaña 2 (Biblioteca):**
   - Contiene un `QWebEngineView` que carga `/library` a pantalla completa.
4. **QWebChannel Integration:**
   - Instanciar `QWebChannel` y registrar el `JSBridge`.
   - Asignar el canal a ambas vistas web:
     `view->page()->setWebChannel(channel);`

---

## 3. Detalle de los Cambios React (Vite)

### A. Servidor Dev y Enrutamiento Simple
La interfaz detectará la ruta (`window.location.pathname`) para mostrar el panel correspondiente:
- Si es `/chat`, renderiza la vista de chat (barra lateral).
- Si es `/library`, renderiza la vista de biblioteca (grafo y tabla).

### B. Integración del Cliente WebChannel
Usaremos un wrapper de `qwebchannel.ts` en TypeScript que expone la conexión global:
```typescript
declare global {
  interface Window {
    qt: {
      webChannelTransport: any;
    };
    qtBridge?: any;
  }
}
```

---

## 4. Instalación de Dependencias de Compilación en Fedora

Para compilar `QtWebEngine` se requiere instalar el paquete de desarrollo correspondiente en Fedora:
```bash
sudo dnf install -y qt6-qtwebengine-devel
```

---

## 5. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación de este plan técnico:
1. Realizaremos un **commit en git** con la planificación aprobada.
2. Escribiremos el **Plan de Implementación** detallando los comandos NPM y el orden secuencial de creación de archivos.
