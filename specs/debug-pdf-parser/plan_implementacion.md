# Plan de Implementación: Spec - Debug PDF Parser

Este plan detalla la estrategia paso a paso para la implementación del servicio de dibujo, los endpoints de la API y la interfaz HTML del depurador visual.

---

## 1. Estrategia de Ejecución (Paso a Paso)

El desarrollo se realizará de forma secuencial directa por el agente principal.

### Paso 1: Codificación del Servicio de Dibujo (`backend/app/services/pdf_debug.py`)
1. Importar `fitz` y el comparador `compare_blocks` desde `app.services.pdf_parser`.
2. Implementar `draw_debug_annotations(file_bytes: bytes, page_number: int) -> bytes`:
   * Abrir el PDF y cargar la página especificada.
   * Obtener los bloques y filtrarlos.
   * Ordenar los bloques usando el comparador topológico 2D.
   * Dibujar bounding boxes en rojo, coordenadas en azul y los números de orden correspondientes centrados en amarillo/verde.
   * Retornar los bytes del renderizado PNG.

### Paso 2: Desarrollo de Endpoints (`backend/app/api/v1/endpoints/debug.py`)
1. Implementar la subida temporal de archivos.
2. Implementar el endpoint que sirve el PNG anotado.
3. Diseñar la página HTML responsiva y embeberla en el endpoint `/ui`:
   * Interfaz limpia con barra de herramientas superior, carga de archivos y área de visualización.
   * Navegación interactiva utilizando Vanilla JS.

### Paso 3: Registro en el Enrutador (`backend/app/api/v1/router.py`)
1. Modificar el enrutador para incluir el módulo `debug` bajo el prefijo `/debug`.

### Paso 4: Pruebas y Validación de Calidad
1. Ejecutar las pruebas locales para verificar que no haya regresiones.
2. Ejecutar Ruff para verificar el linter y formatear el código.
3. Proporcionar instrucciones para levantar el servidor y probar la UI en el navegador.

---

## 2. Próxima Fase (Fase 4: Implementación de Código)
Tras recibir la aprobación del usuario para este Plan de Implementación:
1. Realizaremos un **commit en git** con el plan de desarrollo aprobado.
2. Procederemos a la creación física de los archivos.
