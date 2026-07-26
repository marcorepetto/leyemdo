# Formulario de Requisitos: Spec 5 - Servicios de Acción Contextual

Este formulario tiene como objetivo definir decisiones técnicas y de comportamiento del producto para la **Spec 5: Servicios de Acción Contextual**.

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para proceder a la planificación técnica de esta especificación.

---

## 1. Tipo de Respuesta (JSON vs Streaming SSE)
Para las acciones de **Explicar** y **Traducir**:
* **JSON Simple (Sugerido):** Retorna la respuesta completa de una sola vez. Es más fácil de implementar y perfecto para Tooltips o diálogos emergentes rápidos que no distraigan de la lectura.
* **Server-Sent Events (SSE):** Transmite la respuesta palabra por palabra en streaming. Aporta dinamismo visual si el fragmento a explicar es muy largo.
* **Opciones:**
  - [x] JSON Simple (Recomendado para tooltips y ventanas emergentes inline)
  - [ ] Streaming SSE (Igual que el chat conversacional)

---

## 2. Enfoque Didáctico (ZDP) en Explicaciones Rápidas
En el chat principal, el LLM actúa como un tutor pedagógico usando la metodología ZDP (andamiaje), haciendo contra-preguntas en lugar de dar respuestas directas.
* **¿Deseas mantener este enfoque pedagógico estricto (ZDP) en la ventana contextual de explicación rápida, o prefieres una respuesta directa y concisa?**
  - [ ] Mantener ZDP (el popup contextual también retará cognitivamente al usuario)
  - [x] Explicación directa y concisa (Recomendado para no interrumpir el flujo de lectura del paper)

---

## 3. Reranking en Búsqueda Relacionada
La Spec 4 implementó un sistema de Reranking con `nvidia/llama-nemotron-rerank-vl-1b-v2:free` para la búsqueda general.
* **¿Debería aplicarse Reranking también en la búsqueda de documentos relacionados (`/api/v1/context/search-related`)?**
  - [x] Sí (Mejora la calidad de los documentos relacionados que se proponen)
  - [ ] No (Usa búsqueda de similitud vectorial pura en LanceDB para menor tiempo de respuesta)

---

## 4. Estructura de Respuesta de Soporte Interno
La acción de soporte interno busca fragmentos dentro del mismo PDF.
* **¿Qué datos mínimos necesita el visor para resaltar las secciones complementarias?**
  - [x] Número de página física (`page_number`), texto del fragmento y score de similitud. (Recomendado)
  - [ ] Además, coordenadas de caracteres en la página (`char_start` y `char_end`).
  - [ ] Otra (especificar): 
