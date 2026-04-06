"""
Backfill daily OHLCV bars from yfinance for dates before our minute-level data.

Fetches 1-day interval bars for the full year (ytd) and inserts only rows
that don't already exist in price_data (ON CONFLICT DO NOTHING).

Run after fetch_yfinance.py to give "this year" queries full coverage.
"""
import asyncio
import asyncpg
import yfinance as yf
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

YF_SYMBOL_MAP = {
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
}

INSTRUMENTS = [
    ("AAPL",          "Apple Inc.",               "Technology",        "NASDAQ"),
    ("GOOGL",         "Alphabet Inc.",             "Technology",        "NASDAQ"),
    ("MSFT",          "Microsoft Corp.",           "Technology",        "NASDAQ"),
    ("AMZN",          "Amazon.com Inc.",           "Consumer Cyclical", "NASDAQ"),
    ("TSLA",          "Tesla Inc.",                "Consumer Cyclical", "NASDAQ"),
    ("META",          "Meta Platforms",            "Technology",        "NASDAQ"),
    ("NVDA",          "NVIDIA Corp.",              "Technology",        "NASDAQ"),
    ("NFLX",          "Netflix Inc.",              "Communication",     "NASDAQ"),
    ("AMD",           "Advanced Micro Devices",    "Technology",        "NASDAQ"),
    ("INTC",          "Intel Corp.",               "Technology",        "NASDAQ"),
    ("PYPL",          "PayPal Holdings",           "Financial",         "NASDAQ"),
    ("SHOP",          "Shopify Inc.",              "Technology",        "NYSE"),
    ("CRM",           "Salesforce Inc.",           "Technology",        "NYSE"),
    ("ORCL",          "Oracle Corp.",              "Technology",        "NYSE"),
    ("IBM",           "IBM Corp.",                 "Technology",        "NYSE"),
    ("GLD",           "SPDR Gold Shares",          "Commodity",         "NYSE Arca"),
    ("SLV",           "iShares Silver Trust",      "Commodity",         "NYSE Arca"),
    ("SPY",           "S&P 500 ETF (SPY)",         "Index",             "NYSE Arca"),
    ("QQQ",           "NASDAQ 100 ETF (QQQ)",      "Index",             "NASDAQ"),
    ("DIA",           "Dow Jones ETF (DIA)",       "Index",             "NYSE Arca"),
    ("NIFTY50",       "Nifty 50 Index",            "Index",             "NSE"),
    ("SENSEX",        "BSE Sensex",                "Index",             "BSE"),
    ("RELIANCE.NS",   "Reliance Industries",       "Energy",            "NSE"),
    ("TCS.NS",        "Tata Consultancy Services", "Technology",        "NSE"),
    ("INFY.NS",       "Infosys Ltd.",              "Technology",        "NSE"),
    ("HDFCBANK.NS",   "HDFC Bank",                 "Financial",         "NSE"),
    ("ICICIBANK.NS",  "ICICI Bank",                "Financial",         "NSE"),
    ("WIPRO.NS",      "Wipro Ltd.",                "Technology",        "NSE"),
    ("HCLTECH.NS",    "HCL Technologies",          "Technology",        "NSE"),
    ("BAJFINANCE.NS", "Bajaj Finance",             "Financial",         "NSE"),
    ("KOTAKBANK.NS",  "Kotak Mahindra Bank",       "Financial",         "NSE"),
    ("LT.NS",         "Larsen & Toubro",           "Industrials",       "NSE"),
]


async def backfill_symbol(conn, symbol: str) -> int:
    yf_ticker = YF_SYMBOL_MAP.get(symbol, symbol)
    try:
        ticker = yf.Ticker(yf_ticker)
        # Fetch full YTD daily bars
        df = ticker.history(start="2026-01-01", end="2026-04-07", interval="1d")
        if df.empty:
            print(f"  {symbol}: no daily data")
            return 0
        df = df.reset_index()
        col = "Date" if "Date" in df.columns else "Datetime"
        df[col] = pd.to_datetime(df[col]).dt.tz_localize("UTC") if df[col].dt.tz is None else pd.to_datetime(df[col]).dt.tz_convert("UTC")
        rows = [
            (symbol,
             row[col],
             round(float(row["Open"]),  4),
             round(float(row["High"]),  4),
             round(float(row["Low"]),   4),
             round(float(row["Close"]), 4),
             int(row["Volume"]))
            for _, row in df.iterrows()
        ]
        if rows:
            await conn.executemany(
                "INSERT INTO price_data VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT DO NOTHING",
                rows,
            )
        print(f"  {symbol}: {len(rows)} daily bars inserted (skips existing)")
        return len(rows)
    except Exception as e:
        print(f"  {symbol}: ERROR — {e}")
        return 0


async def main():
    conn = await asyncpg.connect(os.getenv("SUPABASE_DB_URL"), ssl="require")
    before = await conn.fetchval("SELECT COUNT(*) FROM price_data")
    print(f"Rows before: {before:,}\nBackfilling daily bars for 2026 YTD...\n")

    total = 0
    for sym, *_ in INSTRUMENTS:
        total += await backfill_symbol(conn, sym)

    after = await conn.fetchval("SELECT COUNT(*) FROM price_data")
    date_range = await conn.fetchrow(
        "SELECT MIN(ts)::date AS start, MAX(ts)::date AS end FROM price_data"
    )
    await conn.close()
    print(f"\nRows after:  {after:,}  (+{after - before:,} new)")
    print(f"Date range:  {date_range['start']} → {date_range['end']}")


if __name__ == "__main__":
    asyncio.run(main())
