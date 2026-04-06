"""Unit tests for services/auth.py — no DB or network required."""
import pytest
from jose import jwt, JWTError
from app.services.auth import hash_password, verify_password, create_jwt, decode_jwt


def test_hash_and_verify_correct_password():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_hash_produces_different_salts():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt uses random salt


def test_create_jwt_returns_string():
    token = create_jwt("user-abc")
    assert isinstance(token, str)
    assert len(token) > 20


def test_decode_jwt_roundtrip():
    user_id = "00000000-0000-0000-0000-000000000042"
    token = create_jwt(user_id)
    assert decode_jwt(token) == user_id


def test_decode_jwt_invalid_token_raises():
    with pytest.raises(Exception):
        decode_jwt("not.a.valid.token")


def test_decode_jwt_tampered_token_raises():
    token = create_jwt("user-1") + "tampered"
    with pytest.raises(Exception):
        decode_jwt(token)
