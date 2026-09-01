"""Implementacion de AIProvider usando un modelo local servido por Ollama."""
import httpx
from ollama import AsyncClient, ResponseError

from app.ai.base import JsonRetryAIProvider
from app.core.config import settings

DEFAULT_MODEL = "qwen2.5-coder:7b"


class OllamaProvider(JsonRetryAIProvider):
    # ConnectionError es lo que tira el SDK de ollama cuando no puede conectarse al server
    # (Ollama no esta corriendo) - no hereda de httpx.HTTPError, hay que catchearlo aparte.
    # httpx.HTTPError cubre timeouts; ResponseError es lo que tira el SDK cuando el server
    # responde un error (ej. el modelo pedido no esta descargado localmente).
    TRANSIENT_ERRORS = (ConnectionError, httpx.HTTPError, ResponseError)

    def __init__(self, host: str | None = None, model: str = DEFAULT_MODEL):
        self._client = AsyncClient(host=host or settings.ollama_host, timeout=30.0)
        self._model = model

    async def _generate_json(self, prompt: str) -> str:
        response = await self._client.chat(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            format="json",  # fuerza salida JSON valida a nivel de sampling, no solo de prompt
            options={"temperature": 0.1},
        )
        return response.message.content or "[]"
