"""Integration tests for /api/auth endpoints — DB is mocked."""
import pytest
from unittest.mock import AsyncMock, patch


_USER_ROW = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "test@meshdefend.dev",
    "display_name": "Test User",
    "password_hash": None,  # filled in per-test
}


# ── Signup ────────────────────────────────────────────────────────────────────

async def test_signup_success(client):
    from app.services.auth import hash_password
    row = {**_USER_ROW, "password_hash": hash_password("secret123")}
    with patch("app.api.auth.create_user", new_callable=AsyncMock, return_value=row):
        resp = await client.post("/api/auth/signup", json={
            "email": "test@meshdefend.dev",
            "password": "secret123",
            "display_name": "Test User",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@meshdefend.dev"


async def test_signup_duplicate_email(client):
    from asyncpg.exceptions import UniqueViolationError
    with patch("app.api.auth.create_user", new_callable=AsyncMock,
               side_effect=UniqueViolationError("dup")):
        resp = await client.post("/api/auth/signup", json={
            "email": "dup@example.com",
            "password": "pass",
        })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client):
    from app.services.auth import hash_password
    row = {**_USER_ROW, "password_hash": hash_password("secret123")}
    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=row):
        resp = await client.post("/api/auth/login", json={
            "email": "test@meshdefend.dev",
            "password": "secret123",
        })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client):
    from app.services.auth import hash_password
    row = {**_USER_ROW, "password_hash": hash_password("correct")}
    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=row):
        resp = await client.post("/api/auth/login", json={
            "email": "test@meshdefend.dev",
            "password": "wrong",
        })
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=None):
        resp = await client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "pass",
        })
    assert resp.status_code == 401


# ── /me ───────────────────────────────────────────────────────────────────────

async def test_me_returns_user(client, auth_headers):
    row = {**_USER_ROW}
    with patch("app.api.auth.get_user_by_id", new_callable=AsyncMock, return_value=row):
        resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@meshdefend.dev"


async def test_me_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 403  # no token → forbidden


async def test_me_invalid_token(client):
    resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


# ── Config endpoint (no auth required) ───────────────────────────────────────

async def test_llm_config_get(client):
    resp = await client.get("/api/config/llm")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert len(data["available_models"]) == 4


async def test_llm_config_post(client):
    resp = await client.post("/api/config/llm", json={
        "provider": "openrouter",
        "model": "openai/gpt-4o-mini",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
    # verify it was applied
    cfg = (await client.get("/api/config/llm")).json()
    assert cfg["provider"] == "openrouter"
