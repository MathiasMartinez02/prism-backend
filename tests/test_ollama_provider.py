"""Tests de OllamaProvider con la llamada al modelo mockeada (no requiere Ollama corriendo)."""
from unittest.mock import AsyncMock

import httpx
import pytest
from ollama import ResponseError

from app.ai.ollama_provider import OllamaProvider


def _make_provider() -> OllamaProvider:
    return OllamaProvider(host="http://localhost:11434")


@pytest.mark.asyncio
async def test_analyze_hunk_parses_valid_json_on_first_try():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        return_value='[{"category": "bug", "severity": "medium", "file_path": "x.py", "description": "x"}]'
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert len(findings) == 1
    assert findings[0].category == "bug"


@pytest.mark.asyncio
async def test_analyze_hunk_retries_once_on_malformed_json_and_succeeds():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        side_effect=[
            "no es json",
            '[{"category": "quality", "severity": "low", "file_path": "x.py", "description": "x"}]',
        ]
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert provider._generate_json.call_count == 2
    assert len(findings) == 1


@pytest.mark.asyncio
async def test_analyze_hunk_recovers_from_connection_error_on_retry():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        side_effect=[
            httpx.ConnectError("ollama no esta corriendo"),
            "[]",
        ]
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert provider._generate_json.call_count == 2
    assert findings == []


@pytest.mark.asyncio
async def test_analyze_hunk_discards_hunk_when_ollama_is_not_running():
    # El SDK de ollama tira un ConnectionError builtin (no httpx.HTTPError) cuando no puede
    # conectarse al server - encontrado probando contra un puerto real sin nada escuchando.
    provider = _make_provider()
    provider._generate_json = AsyncMock(side_effect=ConnectionError("Failed to connect to Ollama"))

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert findings == []


@pytest.mark.asyncio
async def test_analyze_hunk_discards_hunk_on_repeated_ollama_response_error():
    provider = _make_provider()
    provider._generate_json = AsyncMock(side_effect=ResponseError("model not found"))

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert findings == []
