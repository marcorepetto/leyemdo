# Visor Base C++ / Qt 6 (Basado en Okular)

Este subproyecto contiene la aplicación de escritorio nativa en C++ y Qt 6 que sirve como visor principal de PDFs, incrustando el KPart de Okular.

---

## 1. Prerrequisitos (Fedora)

Para compilar y ejecutar esta aplicación, instala las dependencias de desarrollo utilizando el gestor de paquetes `dnf`:

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

---

## 2. Compilación

Para compilar el proyecto, sigue los siguientes pasos estándar en una terminal:

1. Crea el directorio de construcción:
   ```bash
   mkdir build
   cd build
   ```

2. Configura el proyecto con CMake:
   ```bash
   cmake ..
   ```

3. Compila el ejecutable:
   ```bash
   make
   ```

Esto generará el ejecutable binario llamado `lector-visor`.

---

## 3. Ejecución

Puedes ejecutar la aplicación pasándole como argumento la ruta absoluta o relativa de un archivo PDF:

```bash
./lector-visor /ruta/al/documento.pdf
```
