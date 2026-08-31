"""Implementacion de AIProvider usando la API de Gemini."""
import json
import logging

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import TypeAdapter, ValidationError

from app.ai.prompts import build_analysis_prompt, build_retry_prompt
from app.ai.provider import AIProvider
from app.core.config import settings
from app.schemas.finding import FindingCreate

# Errores de red/API (timeout, 5xx, rate limit ya agotado el retry del SDK): un hunk que falla
# por esto no debe tirar abajo el analisis completo del PR, se descarta ese hunk puntual.
_TRANSIENT_ERRORS = (httpx.HTTPError, genai_errors.APIError)

logger = logging.getLogger(__name__)

_findings_adapter = TypeAdapter(list[FindingCreate])

DEFAULT_MODEL = "gemini-3.6-flash"
MAX_RETRIES = 1  # una sola reintentada: si el modelo no ajusta al schema en 2 intentos, se descarta el hunk


class GeminiProvider(AIProvider):
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

    # Pide al modelo que analice el hunk y devuelve la lista ya validada de findings.
    # Nunca deja escapar una excepcion: un fallo de red/API o una respuesta que no matchea
    # el schema hacen que este hunk puntual se descarte (lista vacia), no que se caiga
    # el analisis completo del PR. JSON invalido reintenta con un prompt correctivo;
    # un error de red/timeout reintenta el mismo prompt (no es un problema de formato).
    async def analyze_hunk(self, file_path: str, diff_hunk: str, context: str = "") -> list[FindingCreate]:
        prompt = build_analysis_prompt(file_path, diff_hunk, context)
        next_prompt = prompt

        for attempt in range(MAX_RETRIES + 1):
            try:
                raw_response = await self._generate_json(next_prompt)
            except _TRANSIENT_ERRORS as exc:
                if attempt == MAX_RETRIES:
                    # Sin este log, un rate limit agotado se ve identico a "no hay findings"
                    # en la respuesta del endpoint - un problema real quedaria invisible.
                    logger.warning("gemini_provider: descartando hunk de %s tras error de red/API: %s", file_path, exc)
                    return []
                continue  # reintenta con el mismo prompt original, no es un problema de formato

            try:
                data = json.loads(raw_response)
                findings = _findings_adapter.validate_python(data)
                # El modelo a veces "alucina" un file_path distinto; lo forzamos al real.
                return [finding.model_copy(update={"file_path": file_path}) for finding in findings]
            except (json.JSONDecodeError, ValidationError) as exc:
                if attempt == MAX_RETRIES:
                    logger.warning("gemini_provider: descartando hunk de %s, respuesta invalida: %s", file_path, exc)
                    return []
                next_prompt = build_retry_prompt(prompt, raw_response)

        return []
