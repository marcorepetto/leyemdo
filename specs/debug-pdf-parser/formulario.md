# Formulario de Requisitos: Spec - Debug PDF Parser

Este formulario tiene como objetivo definir el alcance, comportamiento y decisiones técnicas clave para la especificación de depuración **Debug PDF Parser**, que permitirá visualizar de manera interactiva cómo el backend extrae y ordena los bloques de texto de un PDF.

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para iniciar la fase de definición.

---

## 1. Método de Renderizado y Dibujo
* **1.1. ¿Cómo prefieres realizar el dibujo de las cajas delimitadoras (bounding boxes) y coordenadas?**
  * [x] **Dibujo directo con PyMuPDF (Recomendado):** Dibujar rectángulos y texto directamente en el objeto página del PDF antes de convertirla a imagen (PNG). Esto evita dependencias de procesamiento de imágenes adicionales y es muy rápido.
  * [ ] **Procesamiento de imagen con Pillow:** Renderizar la página a imagen y luego dibujar encima usando la librería `Pillow` de Python.

---

## 2. Interfaz Web de Depuración
* **2.1. ¿Cómo debe implementarse y servirse la interfaz web?**
  * [x] **HTML/JS Embebido en FastAPI (Recomendado):** Un archivo HTML estático e interactivo (con Tailwind CSS vía CDN y Vanilla JS) servido por un endpoint de FastAPI (ej: `/debug/ui`). Esto permite levantar la UI al instante sin configurar un proyecto React/Node separado.
  * [ ] **React App independiente:** Crear un proyecto frontend separado (añade complejidad de puertos y dependencias en esta etapa).

---

## 3. Visualización de Coordenadas y Orden
* **3.1. ¿Qué esquinas y coordenadas deben visualizarse en cada caja delimitadora (block)?**
  * [x] Esquina superior izquierda `(x0, y0)` y esquina inferior derecha `(x1, y1)` en fuente pequeña (Recomendado, evita la saturación visual).
  * [ ] Las cuatro esquinas del bloque.

* **3.2. ¿Cómo se debe mostrar el número de orden secuencial?**
  * [x] Un número grande y en negrita centrado en el bloque, con un fondo circular semi-transparente para garantizar que sea legible sobre cualquier texto o fondo.
  * [ ] En una esquina del bloque junto a las coordenadas.
