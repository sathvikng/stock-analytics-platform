"""Shared fixtures for all tests."""
import pytest
from unittest.mock import AsyncMock, patch

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_EMAIL = "test@meshdefend.dev"


@pytest.fixture
def auth_token() -> str:
    from app.services.auth import create_jwt
    return create_jwt(TEST_USER_ID)


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def client(auth_token):
    """ASGI test client with migrations stubbed out."""
    from httpx import AsyncClient, ASGITransport
    with patch("app.db.migrations.run_migrations", new_callable=AsyncMock):
        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
