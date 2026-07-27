# Plan de Implementación: Spec 6 - Visor Base Okular

Este plan detalla la estrategia de ejecución paso a paso para implementar el visor base en C++ / Qt 6 utilizando el KPart de Okular en Fedora.

---

## 1. Estrategia de Ejecución (Paso a Paso)

Todo el desarrollo se realizará en una secuencia lógica directa para asegurar la correcta configuración y compilación del entorno gráfico.

### Paso 1: Instalación de las Dependencias de Desarrollo en Fedora
Ejecutar el comando de instalación de paquetes de desarrollo en el sistema para contar con las bibliotecas de Qt 6, KF6 y Okular 6:
```bash
sudo dnf install -y \
    gcc-c++ \
    cmake \
    extra-cmake-modules \
    qt6-qtbase-devel \
    kf6-kparts-devel \
    kf6-kxmlgui-devel \
    kf6-ki18n-devel \
    okular-devel \
    okular-libs \
    okular-part
```

### Paso 2: Creación de la Estructura de Directorios y CMakeLists.txt
1. Crear el directorio `/visor/` en la raíz.
2. Crear la carpeta `/visor/src/` para los archivos fuente.
3. Crear `/visor/CMakeLists.txt` con la configuración de CMake descrita en el Plan Técnico para enlazar Qt 6, KF6 y Okular 6.

### Paso 3: Escritura del Código Fuente C++
1. **Crear `/visor/src/mainwindow.h`:** Declaración de la clase de la ventana principal heredando de `KXmlGuiWindow` y el puntero al KPart de Okular.
2. **Crear `/visor/src/mainwindow.cpp`:**
   - Instanciar el KPart de Okular usando `KParts::PartLoader::instantiatePartForMimeType<KParts::ReadOnlyPart>`.
   - Insertar el widget del KPart en el layout.
   - Ejecutar `setupGUI()` para integrar barras de menú y herramientas nativas.
   - Implementar la función `openDocument()` que abre un PDF usando `openUrl`.
3. **Crear `/visor/src/main.cpp`:**
   - Inicializar `QApplication`.
   - Inicializar `KAboutData` con los metadatos requeridos por KDE (Nombre: "lector-visor", Versión: "0.1.0").
   - Leer el argumento de la línea de comandos para capturar la ruta del PDF.
   - Mostrar la ventana principal y llamar a `openDocument` con la ruta provista.
4. **Crear `/visor/README.md`:** Documento explicativo de los requisitos del sistema y comandos de compilación.

### Paso 4: Compilación y Verificación
1. Crear el directorio `/visor/build/`.
2. Ejecutar `cmake ..` desde el directorio `/visor/build/`.
3. Ejecutar `make` para compilar el proyecto.
4. Verificar la compilación exitosa y la generación del ejecutable `lector-visor`.
5. Ejecutar la aplicación con un archivo PDF de prueba: `./lector-visor /ruta/al/archivo.pdf`.

---

## 2. Plan de Asignación y Paralelización
Dado que el desarrollo requiere configurar y compilar en un único subproyecto C++ secuencialmente, la tarea será ejecutada de forma directa por el agente principal. No se requiere instanciar subagentes.

---

## 3. Próxima Fase (Fase 4: Implementación de Código)
Tras recibir la aprobación de este Plan de Implementación:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Procederemos a realizar la instalación de dependencias, creación de los archivos e inicio de la compilación.
3. Actualizaremos la tabla de estados de las specs en `ETAPAS DE DESARROLLO.md`.
