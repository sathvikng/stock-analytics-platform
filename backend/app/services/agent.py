"""LangGraph 4-node agentic pipeline with SSE streaming."""
import json
import re
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer

from ..db.queries import execute_sql
from ..prompts.symbol_resolution import build_symbol_prompt
from ..prompts.intent_classification import build_intent_prompt
from ..prompts.sql_generation import build_sql_prompt
from ..prompts.analytics_summary import build_analytics_prompt
from ..services.llm import chat_completion, chat_completion_json
from ..services.chart import build_chart_config, needs_chart
from ..services.analytics import _data_range, _pivot

_CONVO_SYSTEM = (
    "You are a helpful stock analytics assistant. "
    "Answer conversationally and concisely. "
    "If asked what you can do, explain that you can query stock prices, volumes, "
    "percent changes, and generate charts from a financial database."
)

# Maps raw DB column names → clean human-readable labels
_COL_LABELS = {
    "ts": "Date", "date": "Date", "period": "Period",
    "open": "Open", "high": "High", "low": "Low", "close": "Close",
    "volume": "Volume", "pct_change": "% Change",
    "symbol": "Symbol", "name": "Name", "sector": "Sector",
}


def _clean_col(name: str) -> str:
    """Return a human-readable column label."""
    return _COL_LABELS.get(name.lower(), name.replace("_", " ").title())


class AgentState(TypedDict):
    query: str
    user_stocks: List[Dict[str, Any]]
    resolved_symbols: List[str]
    intent: Dict[str, Any]
    sql: str
    columns: List[str]
    rows: List[List[Any]]
    chart_config: Optional[Dict[str, Any]]
    direct_answer: Optional[str]


async def resolve_symbols_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    name_map = {s["name"]: s["symbol"] for s in state["user_stocks"] if s.get("name")}
    raw = await chat_completion(build_symbol_prompt(state["query"], name_map))
    symbols = [s.strip() for s in raw.split(",") if s.strip()]
    if symbols:
        writer({"event": "step", "data": {"step": "symbol_resolution", "status": "running", "message": "Resolving symbols..."}})
        writer({"event": "step", "data": {"step": "symbol_resolution", "status": "done", "result": ", ".join(symbols)}})
    return {"resolved_symbols": symbols}


async def generate_sql_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    writer({"event": "step", "data": {"step": "sql_generation", "status": "running", "message": "Analyzing query..."}})
    symbols = [s["symbol"] for s in state["user_stocks"]]
    data_start, data_end = await _data_range()
    intent = await chat_completion_json(
        build_intent_prompt(state["query"], data_start, data_end, symbols, state["resolved_symbols"])
    )
    if intent.get("output_type") == "conversational":
        answer = await chat_completion([
            {"role": "system", "content": _CONVO_SYSTEM},
            {"role": "user", "content": state["query"]},
        ])
        writer({"event": "step", "data": {"step": "sql_generation", "status": "done"}})
        return {"intent": intent, "sql": "", "direct_answer": answer}
    raw_sql = await chat_completion(build_sql_prompt(json.dumps(intent), state["query"]))
    # Strip <think>...</think> blocks (Qwen3/reasoning models), then markdown fences
    sql = re.sub(r"<think>.*?</think>", "", raw_sql, flags=re.DOTALL | re.IGNORECASE)
    sql = re.sub(r"```(?:sql)?", "", sql, flags=re.IGNORECASE).strip().rstrip(";")
    writer({"event": "step", "data": {"step": "sql_generation", "status": "done"}})
    return {"intent": intent, "sql": sql}


async def execute_sql_node(state: AgentState) -> dict:
    if state.get("direct_answer") is not None:
        return {}
    writer = get_stream_writer()
    writer({"event": "step", "data": {"step": "sql_execution", "status": "running", "message": "Querying database..."}})
    rows_dicts = await execute_sql(state["sql"])
    if rows_dicts and "symbol" in rows_dicts[0] and len(rows_dicts[0]) >= 3:
        columns, rows = _pivot(rows_dicts)
        if not columns:
            columns = list(rows_dicts[0].keys())
            rows = [[str(v) if v is not None else None for v in r.values()] for r in rows_dicts]
    elif rows_dicts:
        columns = list(rows_dicts[0].keys())
        rows = [[str(v) if v is not None else None for v in r.values()] for r in rows_dicts]
    else:
        columns, rows = [], []
    # Apply clean labels — prefer alias already in data, else clean the raw name
    clean_columns = [_clean_col(c) for c in columns]
    writer({"event": "step", "data": {"step": "sql_execution", "status": "done"}})
    return {"columns": clean_columns, "rows": rows}


async def build_response_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    if state.get("direct_answer") is not None:
        writer({"event": "result", "data": {
            "type": "answer",
            "data": {"columns": [], "rows": []},
            "chart": None,
            "sql_used": "",
            "intent_summary": state["direct_answer"],
        }})
        return {}
    intent = state.get("intent", {})
    chart_config = None
    if needs_chart(intent) and state.get("columns"):
        writer({"event": "step", "data": {"step": "chart_build", "status": "running", "message": "Building visualization..."}})
        cfg = build_chart_config(intent, state["columns"])
        chart_config = cfg.model_dump() if cfg else None
        writer({"event": "step", "data": {"step": "chart_build", "status": "done"}})

    # Generate LLM analytical summary
    summary = ""
    if state.get("rows"):
        writer({"event": "step", "data": {"step": "insights", "status": "running", "message": "Generating insights..."}})
        summary = await chat_completion(
            build_analytics_prompt(state["query"], state["columns"], state["rows"])
        )
        writer({"event": "step", "data": {"step": "insights", "status": "done"}})

    output_type = "both" if chart_config else "table"
    writer({"event": "result", "data": {
        "type": output_type,
        "data": {"columns": state["columns"], "rows": state["rows"]},
        "chart": chart_config,
        "sql_used": state["sql"],
        "intent_summary": summary,
    }})
    return {"chart_config": chart_config}


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        builder = StateGraph(AgentState)
        builder.add_node("resolve_symbols", resolve_symbols_node)
        builder.add_node("generate_sql", generate_sql_node)
        builder.add_node("execute_sql", execute_sql_node)
        builder.add_node("build_response", build_response_node)
        builder.add_edge(START, "resolve_symbols")
        builder.add_edge("resolve_symbols", "generate_sql")
        builder.add_edge("generate_sql", "execute_sql")
        builder.add_edge("execute_sql", "build_response")
        builder.add_edge("build_response", END)
        _graph = builder.compile()
    return _graph
