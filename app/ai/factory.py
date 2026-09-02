"""Selecciona el AIProvider activo segun la config (env var AI_PROVIDER: gemini | ollama)."""
from app.ai.gemini_provider import GeminiProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.provider import AIProvider
from app.core.config import settings


# Instancia el AIProvider configurado (no cachea entre requests).
def get_ai_provider() -> AIProvider:
    if settings.ai_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("AI_PROVIDER=gemini pero falta GEMINI_API_KEY en el .env")
        return GeminiProvider(api_key=settings.gemini_api_key)

    if settings.ai_provider == "ollama":
        return OllamaProvider(host=settings.ollama_host, model=settings.ollama_model)

    raise ValueError(f"AI_PROVIDER desconocido: '{settings.ai_provider}'")
