"""Logica de retry/validacion compartida entre providers: cada uno solo implementa _generate_json."""
import json
import logging

from pydantic import TypeAdapter, ValidationError

from app.ai.prompts import build_analysis_prompt, build_retry_prompt
from app.ai.provider import AIProvider
from app.schemas.finding import FindingCreate

_findings_adapter = TypeAdapter(list[FindingCreate])

logger = logging.getLogger(__name__)


# Base comun para providers que devuelven JSON en texto libre (Gemini, Ollama). Nunca deja
# escapar una excepcion: separa errores de red/API (reintenta con el mismo prompt) de JSON
# invalido/schema invalido (reintenta con un prompt correctivo). Si se agotan los reintentos,
# el hunk se descarta (lista vacia) en vez de tirar abajo el analisis completo del PR.
class JsonRetryAIProvider(AIProvider):
    MAX_RETRIES = 1  # una sola reintentada: si no ajusta al schema en 2 intentos, se descarta el hunk
    TRANSIENT_ERRORS: tuple[type[Exception], ...] = ()

    # Cada provider implementa esto: le pega al modelo con el prompt dado y devuelve el texto crudo.
    async def _generate_json(self, prompt: str) -> str:
        raise NotImplementedError

    async def analyze_hunk(self, file_path: str, diff_hunk: str, context: str = "") -> list[FindingCreate]:
        prompt = build_analysis_prompt(file_path, diff_hunk, context)
        next_prompt = prompt

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                raw_response = await self._generate_json(next_prompt)
            except self.TRANSIENT_ERRORS as exc:
                if attempt == self.MAX_RETRIES:
                    # Sin este log, un rate limit agotado se ve identico a "no hay findings"
                    # en la respuesta del endpoint - un problema real quedaria invisible.
                    logger.warning(
                        "%s: descartando hunk de %s tras error de red/API: %s",
                        type(self).__name__, file_path, exc,
                    )
                    return []
                continue  # reintenta con el mismo prompt original, no es un problema de formato

            try:
                data = json.loads(raw_response)
                findings = _findings_adapter.validate_python(data)
                # El modelo a veces "alucina" un file_path distinto; lo forzamos al real.
                return [finding.model_copy(update={"file_path": file_path}) for finding in findings]
            except (json.JSONDecodeError, ValidationError) as exc:
                if attempt == self.MAX_RETRIES:
                    logger.warning(
                        "%s: descartando hunk de %s, respuesta invalida: %s",
                        type(self).__name__, file_path, exc,
                    )
                    return []
                next_prompt = build_retry_prompt(prompt, raw_response)

        return []
