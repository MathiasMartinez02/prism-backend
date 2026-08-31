"""Selecciona el AIProvider activo segun la config (env var AI_PROVIDER). Ollama se suma en el bloque 3.1."""
from app.ai.gemini_provider import GeminiProvider
from app.ai.provider import AIProvider
from app.core.config import settings


# Instancia el AIProvider configurado. No cachea: cada request arma su propio provider
# (el cliente de Gemini es liviano de crear, y evita compartir estado entre requests).
def get_ai_provider() -> AIProvider:
    if settings.ai_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("AI_PROVIDER=gemini pero falta GEMINI_API_KEY en el .env")
        return GeminiProvider(api_key=settings.gemini_api_key)

    raise ValueError(f"AI_PROVIDER desconocido: '{settings.ai_provider}'")
