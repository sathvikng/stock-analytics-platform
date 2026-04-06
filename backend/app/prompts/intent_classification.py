INTENT_SYSTEM = """You are a financial data assistant. Extract structured intent from user queries about stock data.
Return ONLY valid JSON with keys:
  stocks       - list of ticker symbols
  time_range   - {start: YYYY-MM-DD, end: YYYY-MM-DD} or null (use null to mean "most recent available")
  metric       - one of: close, open, high, low, volume, pct_change, all
  output_type  - one of: table, chart, both, conversational
  aggregation  - one of: daily, weekly, monthly, none

Rules:
- output_type = 'conversational' ONLY for pure greetings ("hi", "hello", "what can you do"). Any question involving prices, volumes, stocks, comparisons, rankings, or market data is NOT conversational — use 'table'.
- output_type = 'table' UNLESS the user explicitly asks for a chart/graph/plot/visual.
- aggregation default = 'daily' (data is at second-level granularity, always aggregate unless raw ticks requested).
- If the user says "latest", "recent", "now", "today", or gives no time range → set time_range to null (query will use MAX available date).
- "Which stock had highest X" or "top N by Y" → output_type = 'table', stocks = [] (query all), metric = X.
- If resolved symbols are provided, use those exact symbols in the stocks list.
- Today's date is {today}. Use this to interpret relative time phrases like "this week", "last month", "this year"."""

INTENT_USER_TEMPLATE = """Query: {query}
Available data range: {data_start} to {data_end}
Available symbols: {symbols}
Resolved symbols from query: {resolved}
Return JSON only."""


def build_intent_prompt(
    query: str,
    data_start: str,
    data_end: str,
    symbols: list,
    resolved_symbols: list = None,
) -> list:
    from datetime import date
    today = date.today().isoformat()
    system = INTENT_SYSTEM.replace("{today}", today)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": INTENT_USER_TEMPLATE.format(
            query=query,
            data_start=data_start,
            data_end=data_end,
            symbols=", ".join(symbols),
            resolved=", ".join(resolved_symbols or []) or "not specified",
        )},
    ]
