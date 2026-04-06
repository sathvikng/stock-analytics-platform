ANALYTICS_SYSTEM = """You are a concise financial data analyst.
You are given a dataset of stock market results. Write 2-3 sentences of sharp, useful insight.
- Mention key values (highs, lows, trends, notable moves) with exact figures.
- Use $ for USD prices, ₹ for Indian stocks (.NS), % for changes.
- For volume, express large numbers as K (thousands) or M (millions).
- Be direct. No fluff. No "the data shows that"."""

ANALYTICS_USER_TEMPLATE = """Query: {query}
Columns: {columns}
Sample data (first 5 rows): {sample}
Total rows returned: {total_rows}

Write a 2-3 sentence analytical summary of this data."""


def build_analytics_prompt(query: str, columns: list, rows: list) -> list:
    sample = rows[:5]
    return [
        {"role": "system", "content": ANALYTICS_SYSTEM},
        {"role": "user", "content": ANALYTICS_USER_TEMPLATE.format(
            query=query,
            columns=columns,
            sample=sample,
            total_rows=len(rows),
        )},
    ]
