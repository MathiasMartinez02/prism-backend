"""Implementacion de AIProvider usando la API de Gemini."""
import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.ai.base import JsonRetryAIProvider
from app.core.config import settings

DEFAULT_MODEL = "gemini-3.6-flash"


class GeminiProvider(JsonRetryAIProvider):
    # Errores de red/API: se descarta el hunk, no tira abajo el PR.
    TRANSIENT_ERRORS = (httpx.HTTPError, genai_errors.APIError)

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self._client = genai.Client(
            api_key=api_key or settings.gemini_api_key,
            # Recorta el retry/timeout default del SDK para no colgarse varios minutos.
            http_options=types.HttpOptions(
                timeout=20_000,
                retry_options=types.HttpRetryOptions(attempts=2, max_delay=5),
            ),
        )
        self._model = model

    async def _generate_json(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,  # queremos findings consistentes, no creativos
            ),
        )
        return response.text or "[]"
