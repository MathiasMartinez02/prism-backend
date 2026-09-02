"""Configuracion de la app leida desde variables de entorno (.env en desarrollo)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


# Config de la app, validada por pydantic.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://prism:prism@localhost:5432/prism"

    # Origenes permitidos para CORS.
    cors_origins: list[str] = ["http://localhost:3000"]

    github_token: str | None = None

    ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"


# Instancia unica de Settings usada en toda la app.
settings = Settings()
