# Formulario de Requisitos: Spec 4 - Integración de LLM (OpenRouter/Gemini) y Lógica ZDP

Este formulario define el alcance, comportamiento y decisiones técnicas clave para la **Spec 4: Integración de LLM y Lógica ZDP**, de modo que incorpore tanto la generación de embeddings reales como el chat conversacional.

---

## 1. Selección y Configuración de Modelos
* **1.1. ¿Qué proveedor y modelo deseas utilizar por defecto?**
  * [x] **OpenRouter (Recomendado):**
    * Embeddings: `nvidia/nemotron-3-embed-1b:free` (dimensión **2048**).
    * Chat/Completions: `nvidia/nemotron-3-ultra-550b-a55b:free`.
  * [ ] **Google Gemini Nativo:**
    * Embeddings: `text-embedding-004` (dimensión 768).
    * Chat/Completions: `gemini-1.5-flash`.
  * *Respuesta:* OpenRouter (Nemotron) como proveedor principal. La configuración se estructurará de forma flexible en el archivo `.env` para que el software sea agnóstico al modelo.

---

## 2. Enfoque Conversacional y Lógica ZDP (Tutoría)
* **2.1. ¿Cómo debería comportarse el tutor conversacional (andamiaje ZDP)?**
  * [ ] **Modo Socrático Puro:** El tutor nunca proporciona la respuesta directa. Responde con preguntas guía.
  * [x] **Modo Tutor Híbrido (Recomendado):** El tutor explica brevemente los conceptos complejos basándose en el documento, pero inmediatamente plantea una pregunta de seguimiento o un reto conceptual para validar que el usuario ha comprendido el tema.
  * [ ] **Modo Adaptativo:** El usuario puede elegir entre respuesta directa o modo guiado.
  * *Respuesta:* Modo Tutor Híbrido.

* **2.2. ¿Deseas persistir el historial de conversación en la base de datos local (LanceDB) o mantenerlo en memoria por sesión?**
  * [x] **Persistencia en LanceDB (Recomendado):** Creamos una tabla `chat_messages` en LanceDB para que las conversaciones persistan al reiniciar el backend y el usuario pueda retomar lecturas anteriores.
  * [ ] **En memoria (sesión efímera):** El historial de chat se pierde al reiniciar.
  * *Respuesta:* Persistencia en LanceDB (`chat_messages`).

---

## 3. Estrategia de RAG (Retrieval-Augmented Generation)
* **3.1. ¿Cómo debe comportarse el LLM respecto al contexto del documento?**
  * [ ] **Estricto (Soporte Cerrado):** El LLM solo responderá preguntas si la información relevante se encuentra en el contexto del PDF.
  * [x] **Abierto (Soporte Aumentado - Recomendado):** El LLM prioriza el contexto del PDF. Si la respuesta no está allí, utiliza su conocimiento general aclarando al usuario que dicha información no figura explícitamente en el documento original.
  * *Respuesta:* Abierto (Soporte Aumentado).

* **3.2. ¿Cuántos fragmentos de contexto (Top K) enviaremos al prompt de Gemini por defecto?**
  * [ ] 3 fragmentos.
  * [x] 5 fragmentos (Recomendado: balance entre cobertura y velocidad).
  * [ ] 10 fragmentos.
  * *Respuesta:* 5 fragmentos.

---

## 4. Diseño de Endpoints de API y Streaming
* **4.1. ¿Cómo se deben entregar las respuestas del chat?**
  * [x] **Streaming (Server-Sent Events - SSE) (Recomendado):** El backend envía la respuesta palabra por palabra en tiempo real.
  * [ ] **Respuesta JSON estándar (Bloqueante):** El backend responde el mensaje completo en un único bloque.
  * *Respuesta:* Streaming (Server-Sent Events - SSE).

* **4.2. Confirmación de endpoints mínimos a exponer:**
  * `POST /api/v1/chat/message`: Envia una pregunta del usuario, realiza RAG, guarda mensajes en la BD y retorna la respuesta (con soporte para streaming).
  * `GET /api/v1/chat/history/{document_id}`: Recupera el historial de chat asociado a un documento específico.
  * `DELETE /api/v1/chat/history/{document_id}`: Limpia el historial de chat de ese documento.
  * *¿Estás de acuerdo con estos endpoints o deseas añadir/cambiar alguno?*
  * *Respuesta:* Sí, de acuerdo.
