"""Analytics orchestration: standalone helpers + LangGraph run_agent."""
import json
from typing import AsyncGenerator, Optional
from ..db.queries import execute_sql, get_all_stocks, create_session, update_session_time, save_message
from ..prompts.intent_classification import build_intent_prompt
from ..prompts.sql_generation import build_sql_prompt
from ..services.llm import chat_completion, chat_completion_json


async def _data_range() -> tuple[str, str]:
    rows = await execute_sql("SELECT MIN(ts)::date AS d_start, MAX(ts)::date AS d_end FROM price_data")
    r = rows[0]
    return str(r["d_start"]), str(r["d_end"])


async def classify_intent(query: str, resolved_symbols: list = None) -> dict:
    stocks = await get_all_stocks()
    symbols = [s["symbol"] for s in stocks]
    data_start, data_end = await _data_range()
    messages = build_intent_prompt(query, data_start, data_end, symbols, resolved_symbols)
    return await chat_completion_json(messages)


async def generate_sql(intent: dict) -> str:
    messages = build_sql_prompt(json.dumps(intent))
    sql = await chat_completion(messages)
    return sql.strip().rstrip(";")


def _pivot(rows_dicts: list[dict]) -> tuple[list, list]:
    """Pivot rows so each symbol becomes its own column."""
    if not rows_dicts or "symbol" not in rows_dicts[0]:
        return None, None
    x_key = next((k for k in rows_dicts[0] if k in ("date", "ts", "period")), None)
    metric = next((k for k in rows_dicts[0] if k not in ("symbol", x_key)), None)
    if not x_key or not metric:
        return None, None
    symbols = list(dict.fromkeys(str(r["symbol"]) for r in rows_dicts))
    pivot: dict[str, dict] = {}
    for r in rows_dicts:
        key = str(r[x_key])
        pivot.setdefault(key, {x_key: key})
        pivot[key][str(r["symbol"])] = str(r[metric]) if r[metric] is not None else None
    columns = [x_key] + symbols
    return columns, [[row.get(c) for c in columns] for row in pivot.values()]


async def run_query(sql: str) -> tuple[list, list]:
    rows_dicts = await execute_sql(sql)
    if not rows_dicts:
        return [], []
    if "symbol" in rows_dicts[0] and len(rows_dicts[0]) >= 3:
        columns, rows = _pivot(rows_dicts)
        if columns:
            return columns, rows
    columns = list(rows_dicts[0].keys())
    rows = [[str(v) if v is not None else None for v in r.values()] for r in rows_dicts]
    return columns, rows


async def run_agent(
    query: str, user_id: str, session_id: Optional[str]
) -> AsyncGenerator[str, None]:
    """Stream SSE events from the LangGraph pipeline, persisting messages to Supabase."""
    from .agent import get_graph, AgentState

    if not session_id:
        session = await create_session(user_id, query[:80])
        session_id = str(session["id"])
    else:
        await update_session_time(session_id)

    await save_message(session_id, "user", query)

    stocks = await get_all_stocks()
    initial_state: AgentState = {
        "query": query,
        "user_stocks": stocks,
        "resolved_symbols": [],
        "intent": {},
        "sql": "",
        "columns": [],
        "rows": [],
        "chart_config": None,
        "direct_answer": None,
    }

    graph = get_graph()
    final_result_data = None

    try:
        async for chunk in graph.astream(initial_state, stream_mode="custom"):
            if isinstance(chunk, dict) and chunk.get("event") == "result":
                chunk["data"]["session_id"] = session_id
                final_result_data = chunk["data"]
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as exc:
        error_chunk = {"event": "error", "data": {"message": str(exc)}}
        yield f"data: {json.dumps(error_chunk)}\n\n"

    if final_result_data:
        await save_message(
            session_id, "assistant",
            final_result_data.get("intent_summary", ""),
            final_result_data,
        )
        await update_session_time(session_id)

    yield "data: [DONE]\n\n"
