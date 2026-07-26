# Plan de Implementación: Spec 5 - Servicios de Acción Contextual

Este plan detalla los pasos secuenciales para el desarrollo y validación de los servicios de acción contextual en el backend.

---

## 1. Estrategia de Ejecución (Paso a Paso)

### Paso 1: Implementar Plantillas de Prompts
1. Abrir `backend/app/services/prompt_templates.py`.
2. Agregar las variables globales `SYSTEM_PROMPT_EXPLAIN` y `SYSTEM_PROMPT_TRANSLATE`.
3. Implementar e importar las funciones de compilación necesarias para generar los prompts estructurados que se enviarán a OpenRouter.

### Paso 2: Crear Endpoints de Acción Contextual
1. Crear el archivo `backend/app/api/v1/endpoints/context.py`.
2. Definir el esquema Pydantic `ContextActionRequest`.
3. Implementar el endpoint `POST /explain` llamando a la API de OpenRouter/Gemini sin streaming.
4. Implementar el endpoint `POST /translate` para traducciones rápidas y limpias.
5. Implementar el endpoint `POST /search-related` realizando búsqueda vectorial, filtrando los resultados de otros documentos, aplicando Reranking (si está habilitado) y retornando la lista final de chunks.
6. Implementar el endpoint `POST /support` realizando búsqueda vectorial de soporte en el mismo documento.

### Paso 3: Registrar el Router en la API
1. Modificar `backend/app/api/v1/router.py`.
2. Importar `context` desde `app.api.v1.endpoints`.
3. Agregar `api_router.include_router(context.router, prefix="/context", tags=["context"])`.

### Paso 4: Escribir Pruebas Automatizadas
1. Crear el archivo `backend/tests/test_context.py`.
2. Escribir pruebas para validar cada uno de los cuatro endpoints:
   * Test `/explain` (verificando que use correctamente el mock de OpenRouter).
   * Test `/translate` (verificando la estructura de salida y traducción limpia).
   * Test `/search-related` (validando que los fragmentos devueltos pertenezcan a otros documentos).
   * Test `/support` (validando que los fragmentos pertenezcan al mismo documento).

### Paso 5: Ejecución y Validación
1. Ejecutar las pruebas unitarias: `pytest tests/test_context.py` dentro del directorio `backend`.
2. Verificar que no haya lints ni problemas de estilo usando `ruff`.

### Paso 6: Actualización de Estado
1. Una vez aprobadas todas las pruebas y validada la funcionalidad, actualizar la tabla de estado en `ETAPAS DE DESARROLLO.md` marcando la Spec 5 como **Planeada**, **Plan de Des.**, **Implementada** y **Aprobada**.

---

## 2. Plan de Asignación y Paralelización
Toda la lógica de esta Spec se desarrollará directamente en el agente principal de forma secuencial, garantizando una correcta integración del backend con la base de datos local y los modelos de IA antes de pasar a la integración con el visor C++ (Etapa 2).

---

## 3. Próxima Fase (Fase 4: Ejecución)
Tras recibir la aprobación final del usuario para el Plan Técnico y el Plan de Implementación:
1. Realizaremos un commit con los planes aprobados.
2. Iniciaremos el desarrollo del código paso a paso según lo planificado.
