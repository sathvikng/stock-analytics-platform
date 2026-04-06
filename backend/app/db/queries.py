import json as _json
from .client import get_pool
from typing import Any


async def execute_sql(sql: str, *args) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *args)
    return [dict(r) for r in rows]


async def get_all_stocks() -> list[dict]:
    return await execute_sql("SELECT symbol, name, sector, exchange FROM stocks ORDER BY symbol")


async def get_stock_history(symbol: str, start: str, end: str) -> list[dict]:
    sql = "SELECT ts, open, high, low, close, volume FROM price_data WHERE symbol=$1 AND ts BETWEEN $2 AND $3 ORDER BY ts"
    return await execute_sql(sql, symbol, start, end)


# ── Auth ──────────────────────────────────────────────────────────────────────

async def create_user(email: str, password_hash: str, display_name: str = None) -> dict:
    sql = "INSERT INTO users (email, password_hash, display_name) VALUES ($1, $2, $3) RETURNING id, email, display_name, created_at"
    rows = await execute_sql(sql, email, password_hash, display_name)
    return rows[0] if rows else None


async def get_user_by_email(email: str) -> dict:
    rows = await execute_sql("SELECT * FROM users WHERE email = $1", email)
    return rows[0] if rows else None


async def get_user_by_id(user_id: str) -> dict:
    rows = await execute_sql("SELECT id, email, display_name FROM users WHERE id = $1", user_id)
    return rows[0] if rows else None


# ── Sessions ──────────────────────────────────────────────────────────────────

async def create_session(user_id: str, title: str = "New Chat") -> dict:
    sql = "INSERT INTO chat_sessions (user_id, title) VALUES ($1, $2) RETURNING *"
    rows = await execute_sql(sql, user_id, title)
    return rows[0] if rows else None


async def get_sessions(user_id: str) -> list[dict]:
    sql = """SELECT s.id, s.title, s.created_at, s.updated_at,
                    COUNT(m.id)::int AS message_count
             FROM chat_sessions s
             LEFT JOIN chat_messages m ON m.session_id = s.id
             WHERE s.user_id = $1
             GROUP BY s.id ORDER BY s.updated_at DESC"""
    return await execute_sql(sql, user_id)


async def update_session_time(session_id: str) -> None:
    await execute_sql("UPDATE chat_sessions SET updated_at = NOW() WHERE id = $1", session_id)


# ── Messages ──────────────────────────────────────────────────────────────────

async def save_message(session_id: str, role: str, content: str, response_json: Any = None) -> dict:
    rj = _json.dumps(response_json) if response_json is not None else None
    sql = "INSERT INTO chat_messages (session_id, role, content, response_json) VALUES ($1, $2, $3, $4::jsonb) RETURNING *"
    rows = await execute_sql(sql, session_id, role, content, rj)
    return rows[0] if rows else None


async def get_messages(session_id: str) -> list[dict]:
    sql = "SELECT * FROM chat_messages WHERE session_id = $1 ORDER BY created_at"
    rows = await execute_sql(sql, session_id)
    for row in rows:
        rj = row.get("response_json")
        if isinstance(rj, str):
            try:
                row["response_json"] = _json.loads(rj)
            except (ValueError, TypeError):
                pass
    return rows
