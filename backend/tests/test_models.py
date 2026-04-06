"""Unit tests for Pydantic request/response models."""
import pytest
from pydantic import ValidationError
from app.models.request import ChatRequest, SignupRequest, LoginRequest, LLMConfigRequest
from app.models.response import (
    AuthUser, AuthResponse, TableData, ChartConfig, ChatResponse, SessionInfo
)


# ── Request models ────────────────────────────────────────────────────────────

def test_chat_request_minimal():
    r = ChatRequest(query="show AAPL")
    assert r.query == "show AAPL"
    assert r.session_id is None


def test_chat_request_with_session():
    r = ChatRequest(query="hi", session_id="abc-123")
    assert r.session_id == "abc-123"


def test_signup_request_full():
    r = SignupRequest(email="a@b.com", password="pass", display_name="Alice")
    assert r.email == "a@b.com"
    assert r.display_name == "Alice"


def test_signup_request_no_display_name():
    r = SignupRequest(email="a@b.com", password="pass")
    assert r.display_name is None


def test_login_request():
    r = LoginRequest(email="a@b.com", password="pass")
    assert r.email == "a@b.com"


def test_llm_config_request():
    r = LLMConfigRequest(provider="ollama", model="qwen3:8b")
    assert r.provider == "ollama"


# ── Response models ───────────────────────────────────────────────────────────

def test_auth_user_model():
    u = AuthUser(id="uid", email="a@b.com")
    assert u.display_name is None


def test_table_data_model():
    td = TableData(columns=["date", "close"], rows=[["2025-01-01", "150.00"]])
    assert len(td.columns) == 2
    assert len(td.rows) == 1


def test_chart_config_model():
    cc = ChartConfig(chart_type="line", x_key="date", series=["AAPL", "TSLA"])
    assert cc.chart_type == "line"
    assert "AAPL" in cc.series


def test_chat_response_table_only():
    resp = ChatResponse(
        type="table",
        data=TableData(columns=["c"], rows=[["v"]]),
        sql_used="SELECT 1",
        intent_summary="test",
    )
    assert resp.chart is None


def test_chat_response_with_chart():
    resp = ChatResponse(
        type="both",
        data=TableData(columns=["date", "AAPL"], rows=[["2025-01-01", "150"]]),
        chart=ChartConfig(chart_type="line", x_key="date", series=["AAPL"]),
        sql_used="SELECT ...",
        intent_summary="Showing close for AAPL",
    )
    assert resp.chart is not None
    assert resp.chart.chart_type == "line"


def test_chat_response_answer_type():
    resp = ChatResponse(
        type="answer",
        data=TableData(columns=[], rows=[]),
        sql_used="",
        intent_summary="Hello! I can help you with stock data.",
    )
    assert resp.type == "answer"
