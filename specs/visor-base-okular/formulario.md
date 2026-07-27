# Formulario de Requisitos: Spec 6 - Visor Base Okular

Este formulario tiene como objetivo definir el alcance, comportamiento, dependencias y decisiones técnicas clave para la **Spec 6: Visor Base Okular**, que establecerá el visor nativo en C++ / Qt basado en Okular.

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para proceder a la sesión de refinamiento y diseño de la arquitectura.

---

## 1. Estrategia de Fork / Integración de Okular

Okular es un visor maduro que depende de KDE Frameworks. Para su integración, existen tres enfoques posibles:

* **Opción A (Fork Completo):** Clonar un tag o versión específica del repositorio oficial de Okular como subdirectorio/submódulo de este proyecto, y añadir parches para compilarlo con nuestro panel de asistencia.
* **Opción B (Aplicación Qt C++ a Medida con libokularcore):** Crear una aplicación C++ desde cero usando Qt, que enlace de forma dinámica contra la biblioteca del núcleo de Okular (`libokular5core` o `libokular6core`) instalada en el sistema del usuario. Esto reduce la complejidad de compilar todo Okular desde cero.
* **Opción C (Visor Qt Basado en Poppler-Qt sin Okular completo):** Si el objetivo es un visor ligero y personalizado sin la sobrecarga de dependencias de KDE, construir un visor básico usando `poppler-qt5` o `poppler-qt6`. *Nota: Esto cambiaría ligeramente la propuesta inicial, pero simplifica drásticamente el empaquetado.*

**¿Qué enfoque prefieres seguir?**
- [ ] Opción A: Fork completo de Okular (Fiel a la propuesta original, requiere compilar todo KDE Okular).
- [x] Opción B: Aplicación C++/Qt personalizada enlazando `libokularcore` del sistema (Recomendado para balancear control y facilidad de compilación).
- [ ] Opción C: Visor simplificado usando Poppler-Qt sin dependencias de KDE.
- [ ] Otra (especificar): 

---

## 2. Versión de Qt y KDE Frameworks

Okular actualmente migró a Qt 6 / KF6 en sus versiones más recientes, pero Qt 5 / KF5 sigue estando ampliamente extendido y soportado en muchas distribuciones Linux.

* **2.1. ¿Qué versión de Qt y KDE Frameworks deberíamos marcar como objetivo?**
  - [ ] Qt 5 / KF5 (Mayor compatibilidad en sistemas Linux antiguos o LTS).
  - [x] Qt 6 / KF6 (Recomendado, tecnología más moderna y ciclo de vida activo).
  - [ ] Indiferente / Dejar que el compilador del sistema lo decida.

---

## 3. Estructura de Directorios para el Visor

Sugerimos colocar el código del visor en una carpeta raíz `/visor/` (o `/okular/`) paralela a `/backend/`.

* **3.1. ¿Dónde prefieres ubicar el código fuente del visor C++?**
  - [x] `/visor/` (Recomendado)
  - [ ] `/frontend/` (Si planeamos meter ahí tanto C++ como React en carpetas separadas)
  - [ ] Otra (especificar): 

---

## 4. Alcance Inicial (In-Scope vs. Out-of-Scope)

Para esta Spec 6 (Visor **Base**), proponemos los siguientes límites:

* **In-Scope (Qué hace):**
  - Configuración del sistema de construcción CMake para compilar el visor C++.
  - Script o documentación de instalación de dependencias de desarrollo para sistemas basados en Debian/Ubuntu (ej. `apt-get install...`).
  - Creación de la ventana principal de la aplicación en Qt.
  - Carga y visualización básica de un archivo PDF (pasado como argumento por línea de comandos o hardcodeado inicialmente).
  - Integración de los controles básicos de navegación (ir a página, zoom básico, barra de herramientas).
  - Estructura limpia para recibir la vista web embebida en la siguiente spec.

* **Out-of-Scope (Qué NO hace en esta fase):**
  - La vista web embebida `QWebEngineView` o la interfaz React (Spec 7).
  - El puente IPC `QtWebChannel` para comunicación bidireccional (Spec 7).
  - Búsqueda semántica, chat lateral interactivo (Spec 8).
  - El panel de la biblioteca o el grafo de documentos (Spec 9).
  - Intercepción de atajos y selección de texto para enviar a FastAPI (Spec 10).

**¿Estás de acuerdo con este alcance para la Spec 6?**
- [ ] Sí, estoy de acuerdo.
- [x] No, quiero modificar el alcance (especificar): Estoy en fedora, no debian ni ubuntu.

---

## 5. Requisitos del Entorno del Desarrollador

* **5.1. ¿Cuál es tu distribución Linux y gestor de paquetes principal para verificar e instalar las dependencias de desarrollo?** (Ej: Ubuntu 22.04/24.04 con `apt`, Arch Linux con `pacman`, Fedora con `dnf`, etc.)
  - R: Fedora con dnf
