"""Unit tests for in-memory LLM config switcher — no network required."""
import pytest
from app.services.llm import get_llm_config, update_llm_config


@pytest.fixture(autouse=True)
def reset_llm_config():
    """Restore default LLM config after each test."""
    original = get_llm_config()
    yield
    update_llm_config(original["provider"], original["model"])


def test_get_config_returns_dict():
    cfg = get_llm_config()
    assert "provider" in cfg
    assert "model" in cfg


def test_update_config_changes_provider():
    update_llm_config("openrouter", "qwen/qwen3-8b")
    cfg = get_llm_config()
    assert cfg["provider"] == "openrouter"
    assert cfg["model"] == "qwen/qwen3-8b"


def test_update_config_is_reflected_immediately():
    update_llm_config("openrouter", "anthropic/claude-3.5-haiku")
    assert get_llm_config()["model"] == "anthropic/claude-3.5-haiku"


def test_update_back_to_ollama():
    update_llm_config("openrouter", "openai/gpt-4o-mini")
    update_llm_config("ollama", "qwen3:8b")
    cfg = get_llm_config()
    assert cfg["provider"] == "ollama"
    assert cfg["model"] == "qwen3:8b"


def test_config_api_get(client):
    import asyncio

    async def _get():
        from httpx import AsyncClient, ASGITransport
        from unittest.mock import patch, AsyncMock
        with patch("app.db.migrations.run_migrations", new_callable=AsyncMock):
            from app.main import app
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                return await c.get("/api/config/llm")

    resp = asyncio.get_event_loop().run_until_complete(_get())
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "available_models" in data
    assert len(data["available_models"]) == 4
