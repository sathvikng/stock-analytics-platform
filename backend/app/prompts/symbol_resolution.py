SYMBOL_SYSTEM = """You are a financial symbol resolver.
Given a user query and a name-to-symbol map, extract every company/asset name mentioned
and return their matching ticker symbols as a comma-separated list.
Handle plurals, abbreviations, and partials (e.g. "Apple" → "AAPL", "Google" → "GOOGL").
If no specific stocks are mentioned, return an empty string.
Return ONLY the comma-separated symbols, nothing else."""

SYMBOL_USER_TEMPLATE = """Query: {query}

Name → Symbol map:
{name_map}

Return only the matching symbols, comma-separated."""


def build_symbol_prompt(query: str, name_map: dict) -> list:
    map_str = "\n".join(f"{name} → {symbol}" for name, symbol in name_map.items())
    return [
        {"role": "system", "content": SYMBOL_SYSTEM},
        {"role": "user", "content": SYMBOL_USER_TEMPLATE.format(
            query=query, name_map=map_str
        )},
    ]
