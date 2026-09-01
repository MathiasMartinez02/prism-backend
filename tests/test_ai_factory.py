"""Tests del factory que selecciona el AIProvider activo segun settings.ai_provider."""
import pytest

from app.ai.factory import get_ai_provider
from app.ai.gemini_provider import GeminiProvider
from app.ai.ollama_provider import OllamaProvider
from app.core.config import settings


def test_get_ai_provider_returns_gemini_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")

    provider = get_ai_provider()

    assert isinstance(provider, GeminiProvider)


def test_get_ai_provider_raises_if_gemini_selected_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", None)

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_ai_provider()


def test_get_ai_provider_returns_ollama_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    provider = get_ai_provider()

    assert isinstance(provider, OllamaProvider)


def test_get_ai_provider_raises_for_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "chatgpt")

    with pytest.raises(ValueError, match="chatgpt"):
        get_ai_provider()
