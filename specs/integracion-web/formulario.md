# Formulario de Requisitos: Spec 7 - Entorno de Integración Web

Este formulario tiene como objetivo definir el alcance, comportamiento y decisiones técnicas clave para la **Spec 7: Entorno de Integración Web**, que embeberá un panel de React en el visor C++ usando `QWebEngineView` y establecerá un puente IPC bidireccional mediante `Qt WebChannel`.

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para proceder a la sesión de refinamiento y diseño de la arquitectura.

---

## 1. Ubicación y Estructura del Frontend Web

Para desarrollar el panel de la interfaz de usuario (Chat, Grafo y Tabla), utilizaremos React y TypeScript.

* **1.1. ¿Dónde prefieres colocar el directorio del código fuente de React?**
  - [x] `/frontend/` (Recomendado, en la raíz del repositorio, separado del visor C++ y de la carpeta de especificaciones).
  - [ ] `/visor/frontend/` (Como un subdirectorio dentro del proyecto del visor C++).
  - [ ] Otra (especificar): 

* **1.2. ¿Qué herramienta de empaquetado/bundler de React prefieres utilizar?**
  - [x] Vite + React + TypeScript (Recomendado por su velocidad de inicio y desarrollo).
  - [ ] Create React App (CRA).
  - [ ] Rsbuild / Rspack.

---

## 2. Flujo de Desarrollo vs. Producción (Carga de la URL en C++)

Al desarrollar, es útil cargar una URL viva para poder depurar con Hot Module Replacement (HMR). Para producción, es mejor empaquetar el frontend como archivos estáticos.

* **2.1. ¿Cómo cargaremos la interfaz web en `QWebEngineView`?**
  - [x] **Doble modo (Recomendado):**
    - En modo *Debug/Desarrollo*, el visor C++ cargará una variable de entorno o URL local viva (ej. `http://localhost:5173`).
    - En modo *Release/Producción*, el visor C++ cargará el archivo estático compilado (ej. `index.html` generado por Vite) desde el sistema de archivos local o embebido en recursos de Qt (`qrc://`).
  - [ ] **Siempre estático:** El visor C++ solo carga el archivo `index.html` local compilado (requiere compilar React antes de cada prueba).
  - [ ] **Siempre remoto:** El visor C++ requiere que el servidor dev de React esté corriendo siempre.

---

## 3. Disposición del Layout en la Ventana C++

El visor de Okular KPart se cargó como el widget central de la ventana principal. Ahora agregaremos la vista web.

* **3.1. ¿Cómo se colocará el panel lateral web respecto al PDF?**
  - [x] **Panel Lateral Derecho (Recomendado):** Un panel lateral a la derecha con un divisor deslizable (`QSplitter`) para poder ajustar el tamaño de forma flexible entre el PDF y el panel de React.
  - [ ] **Panel Flotante / Desplegable:** Un panel que se desliza por encima del PDF al presionar un botón.
  - [x] **Pestañas:** Pestaña 1: Lector PDF completo; Pestaña 2: Interfaz inteligente de React.

* **3.2. ¿Deberíamos incluir un botón nativo en la barra de herramientas para mostrar/ocultar el panel lateral?**
  - [x] Sí, un botón de alternancia en la barra de herramientas o menú (Recomendado).
  - [ ] No, el panel estará siempre visible en la pantalla.
Comentario: Deberiamos permitir ambas opciones marcadas en 3.1, por defecto panel lateral.

---

## 4. Puente de Comunicación IPC (Qt WebChannel)

Utilizaremos `Qt WebChannel` para la comunicación bidireccional C++ <-> JS. 

* **4.1. ¿Qué tipo de mensajes o API inicial deberíamos registrar en el puente en esta Spec 7?**
  * *Sugeridos para Spec 7 (Básicos para probar que la integración funciona):*
    - Enviar un mensaje de prueba ("Hello from React") a C++, y que C++ imprima un log o devuelva una respuesta de saludo.
    - Notificar a la web desde C++ que el PDF actual ha cambiado o se ha cargado un archivo.
  * **¿Deseas agregar alguna otra acción para la integración básica?**
    - R: Eso está bien

---

## 5. Alcance Inicial (In-Scope vs. Out-of-Scope)

* **In-Scope (Qué hace):**
  - Configuración del subproyecto React en `/frontend/` usando Vite y TypeScript.
  - Actualización de CMake en `/visor/` para requerir `Qt6WebEngineWidgets` y `Qt6WebChannel`.
  - Creación del puente C++ (`JSBridge` heredando de `QObject`) expuesto al WebChannel.
  - Integración del `QWebEngineView` en la ventana principal de C++ mediante un `QSplitter` (al lado derecho del KPart).
  - Inyección del script `qwebchannel.js` en el frontend y establecimiento de la conexión inicial.
  - Implementación de un botón de alternar visibilidad (Show/Hide) de la barra lateral en el visor.
  
* **Out-of-Scope (Qué NO hace en esta fase):**
  - El diseño visual del Chat con citas cliqueables (Spec 8).
  - El grafo de similitud o biblioteca en React (Spec 9).
  - La captura de selección del PDF de Okular y envío por el puente (Spec 10).
