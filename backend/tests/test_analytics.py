"""Unit tests for analytics helpers — no DB or LLM required."""
import pytest
from app.services.analytics import _pivot, run_query
from unittest.mock import patch, AsyncMock


# ── _pivot ────────────────────────────────────────────────────────────────────

def test_pivot_multi_symbol():
    rows = [
        {"date": "2025-01-01", "symbol": "AAPL", "close": 150},
        {"date": "2025-01-01", "symbol": "TSLA", "close": 250},
        {"date": "2025-01-02", "symbol": "AAPL", "close": 155},
        {"date": "2025-01-02", "symbol": "TSLA", "close": 260},
    ]
    cols, data = _pivot(rows)
    assert cols == ["date", "AAPL", "TSLA"]
    assert len(data) == 2
    assert data[0][0] == "2025-01-01"


def test_pivot_single_symbol():
    rows = [
        {"date": "2025-01-01", "symbol": "AAPL", "close": 150},
        {"date": "2025-01-02", "symbol": "AAPL", "close": 155},
    ]
    cols, data = _pivot(rows)
    assert "AAPL" in cols
    assert "symbol" not in cols


def test_pivot_no_symbol_column_returns_none():
    rows = [{"date": "2025-01-01", "close": 150}]
    cols, data = _pivot(rows)
    assert cols is None
    assert data is None


def test_pivot_preserves_none_values():
    rows = [
        {"date": "2025-01-01", "symbol": "AAPL", "close": None},
        {"date": "2025-01-01", "symbol": "TSLA", "close": 250},
    ]
    cols, data = _pivot(rows)
    aapl_idx = cols.index("AAPL")
    tsla_idx = cols.index("TSLA")
    assert data[0][aapl_idx] is None
    assert data[0][tsla_idx] == "250"


# ── run_query ─────────────────────────────────────────────────────────────────

async def test_run_query_empty_result():
    with patch("app.services.analytics.execute_sql", new_callable=AsyncMock, return_value=[]):
        cols, rows = await run_query("SELECT 1")
    assert cols == []
    assert rows == []


async def test_run_query_simple_flat():
    mock_rows = [{"symbol": "AAPL", "pct_change": 3.14}]
    with patch("app.services.analytics.execute_sql", new_callable=AsyncMock, return_value=mock_rows):
        cols, rows = await run_query("SELECT symbol, pct_change FROM price_data")
    assert cols == ["symbol", "pct_change"]
    assert rows[0] == ["AAPL", "3.14"]


async def test_run_query_pivots_multi_symbol():
    mock_rows = [
        {"date": "2025-01-01", "symbol": "AAPL", "close": 150},
        {"date": "2025-01-01", "symbol": "TSLA", "close": 250},
    ]
    with patch("app.services.analytics.execute_sql", new_callable=AsyncMock, return_value=mock_rows):
        cols, rows = await run_query("SELECT ...")
    assert "AAPL" in cols
    assert "TSLA" in cols
    assert "symbol" not in cols


async def test_run_query_converts_none_to_none():
    mock_rows = [{"date": "2025-01-01", "close": None}]
    with patch("app.services.analytics.execute_sql", new_callable=AsyncMock, return_value=mock_rows):
        cols, rows = await run_query("SELECT ...")
    assert rows[0][1] is None
