"""Live market data via yfinance (Yahoo Finance — no API key required)."""
import yfinance as yf
from datetime import datetime, timezone

YF_SYMBOL_MAP: dict[str, str] = {
    "NIFTY50": "^NSEI",
    "SENSEX":  "^BSESN",
}


def _yf_sym(symbol: str) -> str:
    return YF_SYMBOL_MAP.get(symbol, symbol)


def _pct(current: float, prev: float) -> float:
    return round((current - prev) / prev * 100, 4) if prev else 0.0


def get_quote(symbol: str) -> dict:
    ticker = yf.Ticker(_yf_sym(symbol))
    info = ticker.fast_info
    price = float(info.last_price or 0)
    prev = float(info.previous_close or price)
    return {
        "symbol": symbol,
        "price": round(price, 4),
        "change": round(price - prev, 4),
        "pct_change": _pct(price, prev),
        "volume": int(info.three_month_average_volume or 0),
        "market_cap": int(info.market_cap or 0),
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def get_intraday(symbol: str, period: str = "1d", interval: str = "1m") -> list[dict]:
    df = yf.download(_yf_sym(symbol), period=period, interval=interval,
                     progress=False, auto_adjust=True)
    if df.empty:
        return []
    df.index = df.index.tz_convert("UTC")
    return [
        {"ts": str(idx), "open": round(float(r["Open"]), 4), "high": round(float(r["High"]), 4),
         "low": round(float(r["Low"]), 4), "close": round(float(r["Close"]), 4),
         "volume": int(r["Volume"])}
        for idx, r in df.iterrows()
    ]
