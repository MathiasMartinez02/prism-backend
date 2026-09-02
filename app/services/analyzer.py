"""Orquesta el pipeline: diff -> hunks -> AIProvider -> findings."""
import asyncio

from app.ai.provider import AIProvider
from app.schemas.finding import FindingCreate
from app.services.diff_parser import parse_diff

# Tope de llamadas concurrentes al AIProvider, para no pegar contra el rate limit.
MAX_CONCURRENT_AI_CALLS = 3


# Analiza un diff completo: lo parte en hunks y le pide findings al provider.
async def analyze_diff(provider: AIProvider, diff_text: str) -> list[FindingCreate]:
    hunks = parse_diff(diff_text)
    if not hunks:
        return []

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_AI_CALLS)

    async def _analyze_hunk(hunk) -> list[FindingCreate]:
        async with semaphore:
            return await provider.analyze_hunk(hunk.file_path, hunk.content)

    results = await asyncio.gather(*(_analyze_hunk(hunk) for hunk in hunks))
    return [finding for hunk_findings in results for finding in hunk_findings]
