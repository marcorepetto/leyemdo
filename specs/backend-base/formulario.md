# Formulario de Requisitos: Spec 1 - Backend Base

Este formulario tiene como objetivo definir el alcance, comportamiento y decisiones técnicas clave para la **Spec 1: Backend Base**, que servirá de cimiento para el resto del backend (parsing, embeddings, base de datos vectorial y servicios de IA).

Por favor, responde a las siguientes preguntas o confirma las opciones sugeridas para poder proceder a la sesión de refinamiento y diseño de la arquitectura.

---

## 1. Versión de Python y Entorno
* **1.1. ¿Qué versión de Python se debe utilizar como base para el proyecto?**
  - [ ] Python 3.10
  - [x] Python 3.11 (Recomendado)
  - [ ] Python 3.12
  - [ ] Otra (especificar): 

* **1.2. ¿Qué gestor de dependencias prefieres utilizar?**
  * [ ] `pip` con `requirements.txt` / `setup.py`
  * [x] `uv` (herramienta ultrarrápida recomendada en las directrices)
  * [ ] `poetry` (`pyproject.toml`)
  * [ ] `pipenv` / `conda`

---

## 2. Estructura del Proyecto FastAPI
* **2.1. ¿Prefieres una estructura modular (escalable) o una estructura simple/plana?**
  * *Estructura modular recomendada:*
    ```text
    backend/
    ├── app/
    │   ├── api/
    │   │   └── v1/
    │   │       ├── router.py
    │   │       └── endpoints/  <-- Endpoints futuros (ingest, chat, etc.)
    │   ├── core/
    │   │   ├── config.py       <-- Configuración y variables de entorno
    │   │   └── security.py     <-- Seguridad/cors si aplica
    │   ├── models/             <-- Modelos Pydantic / Entidades
    │   ├── services/           <-- Lógica de negocio (IA, Parsing, etc.)
    │   └── main.py             <-- Entrada de FastAPI
    ├── tests/                  <-- Pruebas automatizadas
    ├── .env.example
    └── pyproject.toml / requirements.txt
    ```
  * [x] Estructura modular (Recomendada)
  * [ ] Estructura plana (todo dentro de pocos archivos para desarrollo rápido)
  * [ ] Otra (especificar): 

---

## 3. Configuración y Variables de Entorno
* **3.1. ¿Utilizaremos `pydantic-settings` para la validación y tipado de variables de entorno?**
  * [x] Sí (Recomendado)
  * [ ] No (usar `os.getenv` tradicional)

* **3.2. ¿Qué variables de entorno iniciales deberíamos configurar además de las básicas (Host, Puerto, CORS)?**
  * *Sugeridas:*
    * `GEMINI_API_KEY` (Obligatoria para la integración de IA posterior)
    * `DATABASE_URL` / `VECTOR_DB_PATH` (Para LanceDB/SQLite-vec en Spec 3)
    * `LOG_LEVEL` (INFO/DEBUG)
  * *Especifica si necesitas alguna otra:* R: Esas están bien por ahora. 

---

## 4. Servidor de Desarrollo y Despliegue
* **4.1. ¿Cómo se ejecutará el servidor en desarrollo local?**
  * [x] Ejecución directa mediante `uvicorn app.main:app --reload`
  * [ ] Docker / Docker Compose (para aislar el entorno)
  * [ ] Un script helper en Bash/Python

---

## 5. Pruebas y Calidad de Código
* **5.1. ¿Qué framework de pruebas automáticas debemos configurar en esta etapa?**
  * [x] `pytest` + `httpx` (para pruebas de endpoints de FastAPI)
  * [ ] Ninguno por ahora
  * [ ] Otro (especificar): 

* **5.2. ¿Debemos incorporar linters / formateadores en el entorno de desarrollo desde el inicio?**
  * [x] Sí, `ruff` (recomendado para linting y formateado rápido)
  * [ ] Sí, `black` + `flake8`
  * [ ] No en esta etapa
