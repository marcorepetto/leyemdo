from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Lector PDF Inteligente API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "openrouter"  # "openrouter", "gemini" o "mock"
    EMBEDDING_MODEL: str = "nvidia/nemotron-3-embed-1b:free"
    EMBEDDING_DIMENSION: int = 2048
    LLM_PROVIDER: str = "openrouter"  # "openrouter" o "gemini"
    LLM_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    RERANK_MODEL: str = "nvidia/llama-nemotron-rerank-vl-1b-v2:free"
    VECTOR_DB_PATH: str = "data/vector_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
