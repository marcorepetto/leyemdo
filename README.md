**Resumen**

La idea consiste en desarrollar una aplicación de escritorio nativa para la lectura y estudio de documentos PDF, complementada con un sistema de inteligencia artificial que permita consultar y comprender el contenido de manera más eficiente. En lugar de tratar al documento como un simple archivo para visualizar, la aplicación lo transforma en una fuente de conocimiento sobre la que es posible realizar consultas en lenguaje natural.

El funcionamiento general se basa en procesar el contenido textual de los documentos, convertirlo en una representación que facilite la búsqueda semántica y almacenar esa información en una base de datos vectorial. Cuando el usuario realiza una consulta, el sistema recupera los fragmentos más relevantes del documento y los proporciona como contexto a un modelo de lenguaje, que genera una respuesta fundamentada en el contenido del propio texto.

La implementación se plantea como una aplicación de escritorio desarrollada sobre un lector de PDF nativo, incorporando una capa de procesamiento documental, generación de embeddings, almacenamiento vectorial e integración con un modelo de lenguaje. Esta arquitectura permite mantener un bajo consumo de recursos, aprovechar las capacidades de un lector de PDF tradicional y añadir funcionalidades de asistencia inteligente para apoyar la lectura y el estudio.

---

## Metodología de Desarrollo: Spec Driven Development (SDD)

Para el desarrollo del proyecto, se utilizará estrictamente la metodología de desarrollo basada en especificaciones (Spec Driven Development). Para cada petición de desarrollo que realice el usuario, a menos que se indique lo contrario, se seguirá el siguiente flujo estructurado de fases:

### Estructura de Carpetas
Todas las especificaciones se organizarán en la carpeta `/specs/` en la raíz del repositorio, creando una subcarpeta específica por cada petición o funcionalidad a desarrollar (ej. `/specs/nombre-de-la-spec/`).

---

### Fases del Ciclo de Vida de una Spec

#### 1. Fase de Definición (Sin Código)
* **Inicio y Creación:** Al recibir la petición, el agente creará una carpeta en `/specs/` para la nueva spec.
* **Formulario del Usuario:** El agente redactará un documento markdown de formulario (`formulario.md`) con preguntas específicas sobre los requisitos, comportamiento y alcance de la funcionalidad.
* **Sesión de Refinamiento (Grill-Me):** Basado en las respuestas del usuario, se utilizará la técnica/herramienta `/grill-me` (o el skill `grill-with-docs`) para cuestionar, stress-testar y resolver cualquier ambigüedad técnica restante.
* **Límites de la fase:** **NO se implementa código de ninguna forma**. Solo se define:
  * Qué es la spec y qué problemas resuelve.
  * Qué hace y qué **no** hace (límites del alcance).
  * Cómo se planea que lo haga a nivel de arquitectura e ingeniería de software (diagramas, flujos de datos).
* **Transición:** El paso a la siguiente fase requiere la aprobación explícita y de viva voz del usuario. El agente **nunca** decide avanzar de fase autónomamente.

#### 2. Fase de Planificación (Plan Técnico)
* **Diseño Técnico e Impacto:** Se define con precisión cómo se implementará la funcionalidad, qué archivos del repositorio se crearán o modificarán, y cómo se integrará con las funcionalidades existentes.
* **Aprobación:** Requiere aprobación explícita del usuario para poder avanzar.

#### 3. Fase de Plan de Implementación (Estrategia y Paralelización)
* **Estrategia de Ejecución:** El agente define un plan de implementación ordenado y sugiere un equipo de subagentes para paralelizar el desarrollo (en caso de que la complejidad y modularidad lo permitan).
* **Aprobación:** El usuario debe aprobar este plan para iniciar la escritura de código.

#### 4. Fase de Implementación (Código e Iteración)
* **Escritura de Código:** Se desarrolla la funcionalidad conforme al plan aprobado.
* **Iteración:** Si hay errores o la implementación no convence al usuario, se corrigen los problemas e itera sobre esta fase hasta alcanzar la conformidad.

---

### Convenciones de Desarrollo y Control de Versiones (Git)
* **Feedback mediante Artifacts:** Cada vez que se modifique algún documento de planificación o definición, el agente enviará un *artifact* al usuario para recibir su retroalimentación inmediata.
* **Ramas de Git:** Al inicio de cada petición, se debe definir explícitamente en qué rama de git se trabajará y cuál será su rama base. El nombre de la rama no debe contener la palabra "spec" y debe seguir el formato `{modulo}/{titulo-breve}` (ej. `backend/backend-base` partiendo de `main`).
* **Hitos de Commit:** Se realizará un *commit* en git al finalizar y ser aprobada cada una de las siguientes etapas principales para asegurar puntos de restauración limpios:
  1. Aprobación de la **Definición**.
  2. Aprobación de la **Planificación**.
  3. Aprobación del **Plan de Implementación**.
  4. Fin de cada **iteración de implementación** (especialmente si hay correcciones de errores o cambios sugeridos por el usuario).

---

## Planificación de Specs

El plan detallado de fases, la secuenciación del desarrollo, la viabilidad de paralelización y la matriz de estados de implementación se encuentran documentados en el archivo:
* **[ETAPAS DE DESARROLLO.md](file:///home/mrepetto/Documentos/lectura/ETAPAS%20DE%20DESARROLLO.md)**
