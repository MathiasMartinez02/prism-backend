"""Implementacion de AIProvider usando la API de Gemini."""
import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.ai.base import JsonRetryAIProvider
from app.core.config import settings

DEFAULT_MODEL = "gemini-3.6-flash"


class GeminiProvider(JsonRetryAIProvider):
    # Errores de red/API (timeout, 5xx, rate limit ya agotado el retry del SDK): un hunk que
    # falla por esto se descarta puntualmente (ver JsonRetryAIProvider), no tira abajo el PR.
    TRANSIENT_ERRORS = (httpx.HTTPError, genai_errors.APIError)

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self._client = genai.Client(
            api_key=api_key or settings.gemini_api_key,
            # El default del SDK reintenta hasta 5 veces con backoff exponencial (hasta ~60s
            # de delay entre intentos): si hay rate limit, el pipeline se puede colgar varios
            # minutos por hunk. Achicamos eso y dejamos que nuestro propio retry (analyze_hunk)
            # decida que hacer con la falla en vez de esperar en silencio.
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
