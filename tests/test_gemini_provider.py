"""Tests de GeminiProvider con la llamada al modelo mockeada (sin gastar cuota real de la API)."""
from unittest.mock import AsyncMock

import httpx
import pytest

from app.ai.gemini_provider import GeminiProvider


def _make_provider() -> GeminiProvider:
    # api_key ficticia: no se usa una vez que _generate_json esta mockeado.
    return GeminiProvider(api_key="test-key")


@pytest.mark.asyncio
async def test_analyze_hunk_parses_valid_json_on_first_try():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        return_value='[{"category": "bug", "severity": "high", "file_path": "x.py", '
        '"line_number": 3, "description": "Off by one", "recommendation": "Use <="}]'
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert len(findings) == 1
    assert findings[0].category == "bug"
    assert findings[0].severity == "high"


@pytest.mark.asyncio
async def test_analyze_hunk_returns_empty_list_when_model_reports_no_issues():
    provider = _make_provider()
    provider._generate_json = AsyncMock(return_value="[]")

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert findings == []


@pytest.mark.asyncio
async def test_analyze_hunk_retries_once_on_malformed_json_and_succeeds():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        side_effect=[
            "esto no es json valido",
            '[{"category": "quality", "severity": "low", "file_path": "x.py", '
            '"description": "Nombre poco claro"}]',
        ]
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert provider._generate_json.call_count == 2
    assert len(findings) == 1
    assert findings[0].category == "quality"


@pytest.mark.asyncio
async def test_analyze_hunk_gives_up_after_max_retries_and_returns_empty_list():
    provider = _make_provider()
    provider._generate_json = AsyncMock(return_value="esto sigue sin ser json")

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert findings == []


@pytest.mark.asyncio
async def test_analyze_hunk_rejects_response_with_invalid_category():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        side_effect=[
            # "typo" no es una categoria valida del schema -> ValidationError -> retry
            '[{"category": "typo", "severity": "low", "file_path": "x.py", "description": "x"}]',
            "[]",
        ]
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert provider._generate_json.call_count == 2
    assert findings == []


@pytest.mark.asyncio
async def test_analyze_hunk_recovers_from_network_timeout_on_retry():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        side_effect=[
            httpx.ReadTimeout("timed out"),
            '[{"category": "bug", "severity": "low", "file_path": "x.py", "description": "x"}]',
        ]
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert provider._generate_json.call_count == 2
    assert len(findings) == 1


@pytest.mark.asyncio
async def test_analyze_hunk_discards_this_hunk_without_crashing_after_repeated_network_errors():
    provider = _make_provider()
    provider._generate_json = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert findings == []


@pytest.mark.asyncio
async def test_analyze_hunk_forces_the_real_file_path_even_if_model_hallucinates_one():
    provider = _make_provider()
    provider._generate_json = AsyncMock(
        return_value='[{"category": "bug", "severity": "low", "file_path": "otro-archivo.py", '
        '"description": "x"}]'
    )

    findings = await provider.analyze_hunk("x.py", "@@ ... @@")

    assert findings[0].file_path == "x.py"
