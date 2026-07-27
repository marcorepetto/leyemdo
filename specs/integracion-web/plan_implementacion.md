# Plan de Implementación: Spec 7 - Entorno de Integración Web

Este plan detalla la estrategia de ejecución paso a paso para implementar la integración de la interfaz web en React dentro del visor C++ utilizando QWebEngineView y Qt WebChannel.

---

## 1. Estrategia de Ejecución (Paso a Paso)

### Paso 1: Instalar la Dependencia del Sistema en Fedora
Instalar los archivos de cabeceras y desarrollo para `QtWebEngine` en Fedora:
```bash
sudo dnf install -y qt6-qtwebengine-devel
```

### Paso 2: Inicializar el Subproyecto React en `/frontend/`
1. Crear el directorio `/frontend/` en la raíz.
2. De acuerdo a las directrices de creación de proyectos, ejecutar primero el comando de ayuda para conocer las opciones:
   ```bash
   npx -y create-vite@latest --help
   ```
3. Inicializar el proyecto en modo no interactivo con la plantilla de React y TypeScript:
   ```bash
   npx -y create-vite@latest ./ --template react-ts
   ```
4. Instalar las dependencias iniciales usando `npm install`.

### Paso 3: Configurar el Enrutador y qwebchannel.ts en React
1. **Crear `/frontend/src/qwebchannel.ts`:** Adaptación del script de WebChannel oficial de Qt para TypeScript.
2. **Crear `/frontend/src/App.tsx`:** Implementar detección de ruta simple para cargar:
   - `/chat`: Un panel simple con botones para mandar un mensaje de prueba a C++ y un log de mensajes recibidos.
   - `/library`: Una vista de biblioteca de prueba a pantalla completa.
3. **Crear `/frontend/src/main.tsx`:** Ajustar para usar el enrutamiento simple.

### Paso 4: Implementar el Puente de Comunicación en C++
1. **Crear `/visor/src/jsbridge.h` y `/visor/src/jsbridge.cpp`:**
   - Declarar el slot `postMessage(const QString &)` que imprima el texto en la consola de depuración.
   - Declarar la señal `fileLoaded(const QString &)` para notificar la ruta del PDF.
2. **Modificar `/visor/CMakeLists.txt`:** Añadir `WebEngineWidgets` y `WebChannel` en dependencias y linking.
3. **Modificar `/visor/src/mainwindow.h`:**
   - Cambiar clase base a `KParts::MainWindow`.
   - Declarar `QTabWidget *m_tabWidget`.
   - Declarar `QWebEngineView *m_chatView` y `QWebEngineView *m_libraryView`.
   - Declarar `JSBridge *m_bridge` y `QWebChannel *m_channel`.
4. **Modificar `/visor/src/mainwindow.cpp`:**
   - Inicializar el `QTabWidget` como widget central.
   - Configurar `QSplitter` en la primera pestaña con el KPart (izquierda) y `m_chatView` (derecha).
   - Agregar `m_libraryView` en la segunda pestaña.
   - Inicializar `QWebChannel`, registrar `m_bridge` y asociarlo con las vistas web.
   - Conectar la señal de Okular o carga de archivos para emitir `fileLoaded` a través del bridge.

### Paso 5: Compilación y Verificación de la Integración
1. Compilar el visor C++ usando CMake y Make.
2. Levantar el servidor de desarrollo de React con `npm run dev --prefix frontend`.
3. Ejecutar `./visor/build/lector-visor /ruta/a/documento.pdf`.
4. Probar haciendo clic en el botón de prueba de React para ver si llega el mensaje a C++ ("Hello from React").

---

## 2. Plan de Asignación y Paralelización
Toda la implementación se ejecutará de forma directa por el agente principal de manera secuencial, asegurando la sincronización de las librerías C++ y el frontend. No se requiere paralelización con subagentes en esta spec.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Tras recibir la aprobación del usuario para este Plan de Implementación:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Procederemos a ejecutar los comandos e implementar cada uno de los archivos descritos.
