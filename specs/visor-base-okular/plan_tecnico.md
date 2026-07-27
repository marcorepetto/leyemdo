# Plan Técnico: Spec 6 - Visor Base Okular

Este plan técnico detalla la arquitectura de software, los archivos a crear o modificar, y las decisiones de diseño para la implementación de la aplicación de escritorio nativa en C++/Qt 6 basada en Okular.

---

## 1. Archivos Impactados

Crearemos una nueva estructura dedicada `/visor/` en la raíz del repositorio, paralela al directorio `/backend/`.

```text
visor/
├── CMakeLists.txt          # Configuración del build (Qt 6 + KF6 + Okular6)
├── README.md               # Instrucciones de compilación y prerrequisitos en Fedora
└── src/
    ├── main.cpp            # Punto de entrada de la aplicación y KAboutData
    ├── mainwindow.h        # Definición de la clase MainWindow
    └── mainwindow.cpp      # Integración y visualización del KPart de Okular
```

---

## 2. Detalle de los Archivos a Crear

### A. Configuración de Construcción (`visor/CMakeLists.txt`)
Utilizaremos **CMake** como sistema de construcción, buscando de forma estricta las dependencias de Qt 6, KDE Frameworks 6 (KF6) y Okular 6:
* **Qt 6 Modules:** `Widgets`, `Core`
* **KF6 Modules:** `Parts` (para KPart loader), `XmlGui` (para integración de interfaz), `I18n` (internacionalización básica requerida por KDE)
* **Okular:** `Okular6` (para el core de Okular)

```cmake
cmake_minimum_required(VERSION 3.16)
project(lector-visor VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Buscar Dependencias
find_package(Qt6 COMPONENTS Widgets Core REQUIRED)
find_package(KF6 COMPONENTS Parts XmlGui I18n REQUIRED)
find_package(Okular6 REQUIRED)

# Agregar Ejecutable
add_executable(lector-visor
    src/main.cpp
    src/mainwindow.h
    src/mainwindow.cpp
)

# Enlazar Bibliotecas
target_link_libraries(lector-visor
    PRIVATE
    Qt6::Widgets
    Qt6::Core
    KF6::Parts
    KF6::XmlGui
    KF6::I18n
    Okular6
)
```

### B. Punto de Entrada (`visor/src/main.cpp`)
* Inicializa la aplicación Qt usando `QApplication`.
* Configura `KAboutData` (esencial para inicializar el subsistema KParts de KDE, ya que si no se configuran los metadatos de la aplicación, el cargador de plugins fallará o no mostrará las barras de herramientas correctamente).
* Procesa los argumentos de línea de comandos para capturar la ruta del archivo PDF.
* Instancia y muestra `MainWindow`.

### C. Definición de la Ventana Principal (`visor/src/mainwindow.h`)
* Hereda de `KXmlGuiWindow` en lugar de `QMainWindow` para permitir que el KPart de Okular inserte de forma transparente sus menús y barras de herramientas dentro de nuestra ventana principal.
* Declara el puntero a `KParts::ReadOnlyPart`.
* Declara la función para abrir un documento.

```cpp
#pragma once

#include <KXmlGuiWindow>
#include <QUrl>

namespace KParts {
    class ReadOnlyPart;
}

class MainWindow : public KXmlGuiWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

    void openDocument(const QString &filePath);

private:
    void setupVisor();

    KParts::ReadOnlyPart *m_part;
};
```

### D. Implementación de la Ventana (`visor/src/mainwindow.cpp`)
* Utiliza `KParts::PartLoader::instantiatePartForMimeType` para solicitar el componente asociado a `application/pdf`.
* Inserta el widget del KPart (`m_part->widget()`) como el widget central.
* Llama a `setupGUI(Keys | ToolBar | MenuBar | StatusBar)` para fusionar las acciones de Okular en nuestra ventana.
* Llama a `m_part->openUrl(QUrl::fromLocalFile(filePath))` para cargar el documento PDF.

---

## 3. Instalación de Dependencias (Fedora)

Para compilar y ejecutar esta aplicación, se requiere instalar las siguientes herramientas de compilación y librerías de desarrollo en Fedora mediante `dnf`:

```bash
sudo dnf install \
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

---

## 4. Integración y Próximos Pasos
Este visor nativo servirá como el núcleo visual de la aplicación.
Una vez aprobado este Plan Técnico:
1. Realizaremos un **commit en git** con el plan técnico aprobado.
2. Pasaremos a la **Fase 3: Plan de Implementación**, donde detallaremos los archivos exactos con código fuente y prepararemos el entorno para compilar.
