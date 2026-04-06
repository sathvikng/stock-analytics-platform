"""Unit tests for LangGraph agent nodes — LLM and DB are mocked."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_state(**overrides):
    base = {
        "query": "show AAPL close prices",
        "user_stocks": [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Tech", "exchange": "NASDAQ"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Auto", "exchange": "NASDAQ"},
        ],
        "resolved_symbols": [],
        "intent": {},
        "sql": "",
        "columns": [],
        "rows": [],
        "chart_config": None,
        "direct_answer": None,
    }
    return {**base, **overrides}


# ── resolve_symbols_node ──────────────────────────────────────────────────────

async def test_resolve_symbols_finds_apple():
    from app.services.agent import resolve_symbols_node
    mock_writer = MagicMock()
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent.chat_completion", new_callable=AsyncMock, return_value="AAPL"):
        result = await resolve_symbols_node(_make_state(query="show me Apple stock"))
    assert result["resolved_symbols"] == ["AAPL"]
    mock_writer.assert_called()


async def test_resolve_symbols_empty_for_greeting():
    from app.services.agent import resolve_symbols_node
    mock_writer = MagicMock()
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent.chat_completion", new_callable=AsyncMock, return_value=""):
        result = await resolve_symbols_node(_make_state(query="hi"))
    assert result["resolved_symbols"] == []


async def test_resolve_symbols_multiple():
    from app.services.agent import resolve_symbols_node
    mock_writer = MagicMock()
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent.chat_completion", new_callable=AsyncMock, return_value="AAPL, TSLA"):
        result = await resolve_symbols_node(_make_state(query="Apple and Tesla"))
    assert result["resolved_symbols"] == ["AAPL", "TSLA"]


# ── generate_sql_node ─────────────────────────────────────────────────────────

async def test_generate_sql_analytical_query():
    from app.services.agent import generate_sql_node
    mock_writer = MagicMock()
    intent = {"stocks": ["AAPL"], "output_type": "table", "metric": "close", "time_range": None, "aggregation": "daily"}
    sql = "SELECT DATE_TRUNC('day', ts) AS date, close FROM price_data WHERE symbol='AAPL'"
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent._data_range", new_callable=AsyncMock, return_value=("2025-01-01", "2025-12-31")), \
         patch("app.services.agent.chat_completion_json", new_callable=AsyncMock, return_value=intent), \
         patch("app.services.agent.chat_completion", new_callable=AsyncMock, return_value=sql):
        result = await generate_sql_node(_make_state())
    assert result["sql"] == sql
    assert result.get("direct_answer") is None


async def test_generate_sql_conversational_query():
    from app.services.agent import generate_sql_node
    mock_writer = MagicMock()
    intent = {"stocks": [], "output_type": "conversational", "metric": "", "time_range": None, "aggregation": "none"}
    answer = "Hello! I can help you analyse stock data."
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent._data_range", new_callable=AsyncMock, return_value=("2025-01-01", "2025-12-31")), \
         patch("app.services.agent.chat_completion_json", new_callable=AsyncMock, return_value=intent), \
         patch("app.services.agent.chat_completion", new_callable=AsyncMock, return_value=answer):
        result = await generate_sql_node(_make_state(query="hi"))
    assert result["direct_answer"] == answer
    assert result["sql"] == ""


# ── execute_sql_node ──────────────────────────────────────────────────────────

async def test_execute_sql_skips_for_conversational():
    from app.services.agent import execute_sql_node
    state = _make_state(direct_answer="Hello!", sql="")
    result = await execute_sql_node(state)
    assert result == {}  # nothing updated — skipped


async def test_execute_sql_returns_columns_and_rows():
    from app.services.agent import execute_sql_node
    mock_writer = MagicMock()
    db_rows = [{"date": "2025-01-01", "close": 150}]
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent.execute_sql", new_callable=AsyncMock, return_value=db_rows):
        result = await execute_sql_node(_make_state(sql="SELECT date, close FROM price_data"))
    assert result["columns"] == ["date", "close"]
    assert result["rows"] == [["2025-01-01", "150"]]


async def test_execute_sql_handles_empty_result():
    from app.services.agent import execute_sql_node
    mock_writer = MagicMock()
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent.execute_sql", new_callable=AsyncMock, return_value=[]):
        result = await execute_sql_node(_make_state(sql="SELECT ..."))
    assert result["columns"] == []
    assert result["rows"] == []


# ── build_response_node ───────────────────────────────────────────────────────

async def test_build_response_emits_answer_for_conversational():
    from app.services.agent import build_response_node
    mock_writer = MagicMock()
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer):
        result = await build_response_node(_make_state(direct_answer="Hi there!"))
    emitted = mock_writer.call_args[0][0]
    assert emitted["event"] == "result"
    assert emitted["data"]["type"] == "answer"
    assert emitted["data"]["intent_summary"] == "Hi there!"
    assert emitted["data"]["sql_used"] == ""


async def test_build_response_emits_table_for_analytical():
    from app.services.agent import build_response_node
    mock_writer = MagicMock()
    intent = {"output_type": "table", "metric": "close", "stocks": ["AAPL"]}
    state = _make_state(
        intent=intent,
        sql="SELECT ...",
        columns=["date", "close"],
        rows=[["2025-01-01", "150"]],
    )
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent.needs_chart", return_value=False):
        result = await build_response_node(state)
    emitted = mock_writer.call_args[0][0]
    assert emitted["event"] == "result"
    assert emitted["data"]["type"] == "table"
    assert emitted["data"]["chart"] is None


async def test_build_response_includes_chart_when_requested():
    from app.services.agent import build_response_node
    from app.models.response import ChartConfig
    mock_writer = MagicMock()
    intent = {"output_type": "chart", "metric": "close", "stocks": ["AAPL"]}
    fake_chart = ChartConfig(chart_type="line", x_key="date", series=["close"])
    state = _make_state(
        intent=intent,
        sql="SELECT ...",
        columns=["date", "close"],
        rows=[["2025-01-01", "150"]],
    )
    with patch("app.services.agent.get_stream_writer", return_value=mock_writer), \
         patch("app.services.agent.needs_chart", return_value=True), \
         patch("app.services.agent.build_chart_config", return_value=fake_chart):
        result = await build_response_node(state)
    calls = [c[0][0] for c in mock_writer.call_args_list]
    result_event = next(c for c in calls if c.get("event") == "result")
    assert result_event["data"]["type"] == "both"
    assert result_event["data"]["chart"] is not None
