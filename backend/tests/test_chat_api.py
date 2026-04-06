"""Integration tests for /api/chat endpoints — agent and DB are mocked."""
import pytest
import json
from unittest.mock import AsyncMock, patch


async def _fake_run_agent(query, user_id, session_id):
    """Minimal fake SSE generator that emits one step then a result."""
    yield 'data: {"event":"step","data":{"step":"symbol_resolution","status":"running","message":"Resolving..."}}\n\n'
    yield 'data: {"event":"step","data":{"step":"symbol_resolution","status":"done","result":"AAPL"}}\n\n'
    result = {
        "event": "result",
        "data": {
            "type": "table",
            "data": {"columns": ["date", "close"], "rows": [["2025-01-01", "150.00"]]},
            "chart": None,
            "sql_used": "SELECT date, close FROM price_data WHERE symbol='AAPL'",
            "intent_summary": "Showing close for ['AAPL']",
            "session_id": "sess-001",
        },
    }
    yield f"data: {json.dumps(result)}\n\n"
    yield "data: [DONE]\n\n"


async def _fake_run_agent_conversational(query, user_id, session_id):
    result = {
        "event": "result",
        "data": {
            "type": "answer",
            "data": {"columns": [], "rows": []},
            "chart": None,
            "sql_used": "",
            "intent_summary": "Hello! I can help you with stock data analysis.",
            "session_id": "sess-002",
        },
    }
    yield f"data: {json.dumps(result)}\n\n"
    yield "data: [DONE]\n\n"


# ── Streaming endpoint ────────────────────────────────────────────────────────

async def test_chat_stream_requires_auth(client):
    resp = await client.post("/api/chat/stream", json={"query": "show AAPL"})
    assert resp.status_code == 403


async def test_chat_stream_returns_sse(client, auth_headers):
    with patch("app.api.chat.run_agent", side_effect=_fake_run_agent):
        resp = await client.post(
            "/api/chat/stream",
            json={"query": "show AAPL closing prices"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


async def test_chat_stream_contains_step_and_result(client, auth_headers):
    with patch("app.api.chat.run_agent", side_effect=_fake_run_agent):
        resp = await client.post(
            "/api/chat/stream",
            json={"query": "show AAPL closing prices"},
            headers=auth_headers,
        )
    lines = [l for l in resp.text.split("\n") if l.startswith("data:") and "[DONE]" not in l]
    events = [json.loads(l[6:]) for l in lines]
    event_types = [e["event"] for e in events]
    assert "step" in event_types
    assert "result" in event_types


async def test_chat_stream_result_has_session_id(client, auth_headers):
    with patch("app.api.chat.run_agent", side_effect=_fake_run_agent):
        resp = await client.post(
            "/api/chat/stream",
            json={"query": "show AAPL"},
            headers=auth_headers,
        )
    lines = [l for l in resp.text.split("\n") if l.startswith("data:") and "[DONE]" not in l]
    events = [json.loads(l[6:]) for l in lines]
    result = next(e for e in events if e["event"] == "result")
    assert result["data"]["session_id"] == "sess-001"


async def test_chat_stream_conversational_answer(client, auth_headers):
    with patch("app.api.chat.run_agent", side_effect=_fake_run_agent_conversational):
        resp = await client.post(
            "/api/chat/stream",
            json={"query": "hi"},
            headers=auth_headers,
        )
    lines = [l for l in resp.text.split("\n") if l.startswith("data:") and "[DONE]" not in l]
    events = [json.loads(l[6:]) for l in lines]
    result = next(e for e in events if e["event"] == "result")
    assert result["data"]["type"] == "answer"
    assert result["data"]["sql_used"] == ""


# ── Session history endpoints ─────────────────────────────────────────────────

async def test_list_sessions_requires_auth(client):
    resp = await client.get("/api/chat/sessions")
    assert resp.status_code == 403


async def test_list_sessions_returns_list(client, auth_headers):
    fake_sessions = [{"id": "s1", "title": "Test", "created_at": "2025-01-01T00:00:00",
                      "updated_at": "2025-01-01T00:00:00", "message_count": 2}]
    with patch("app.api.chat.get_sessions", new_callable=AsyncMock, return_value=fake_sessions):
        resp = await client.get("/api/chat/sessions", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["sessions"], list)


async def test_get_messages_requires_auth(client):
    resp = await client.get("/api/chat/sessions/abc/messages")
    assert resp.status_code == 403


async def test_get_messages_returns_list(client, auth_headers):
    fake_msgs = [{"id": "m1", "session_id": "s1", "role": "user",
                  "content": "hi", "response_json": None, "created_at": "2025-01-01T00:00:00"}]
    with patch("app.api.chat.get_messages", new_callable=AsyncMock, return_value=fake_msgs):
        resp = await client.get("/api/chat/sessions/s1/messages", headers=auth_headers)
    assert resp.status_code == 200
    msgs = resp.json()["messages"]
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
