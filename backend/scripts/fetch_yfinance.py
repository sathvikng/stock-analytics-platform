"""
Fetch real OHLCV data from yfinance at 1-minute granularity,
then expand each minute bar into 60 second-level rows.

Result: ~60 data points per minute per stock (real prices anchored to yfinance).

yfinance limitation: 1-minute interval is the finest available, max 7 days.
Each minute bar is expanded to 60 rows by linearly interpolating open→close
with small Gaussian noise. Volume is divided evenly across the 60 seconds.
"""
import asyncio
import asyncpg
import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv(Path(__file__).parent.parent / ".env")

# Our internal symbol → yfinance ticker (only where they differ)
YF_SYMBOL_MAP = {
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
}

INSTRUMENTS = [
    # US equities
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
    # Commodity ETFs
    ("GLD",           "SPDR Gold Shares",          "Commodity",         "NYSE Arca"),
    ("SLV",           "iShares Silver Trust",      "Commodity",         "NYSE Arca"),
    # US Index ETFs
    ("SPY",           "S&P 500 ETF (SPY)",         "Index",             "NYSE Arca"),
    ("QQQ",           "NASDAQ 100 ETF (QQQ)",      "Index",             "NASDAQ"),
    ("DIA",           "Dow Jones ETF (DIA)",       "Index",             "NYSE Arca"),
    # Indian Indexes (mapped via YF_SYMBOL_MAP)
    ("NIFTY50",       "Nifty 50 Index",            "Index",             "NSE"),
    ("SENSEX",        "BSE Sensex",                "Index",             "BSE"),
    # Indian equities (.NS suffix is yfinance's NSE format)
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

CREATE_STOCKS = """CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    exchange VARCHAR(20) DEFAULT 'NASDAQ'
);"""

CREATE_PRICE = """CREATE TABLE IF NOT EXISTS price_data (
    symbol VARCHAR(20) REFERENCES stocks(symbol),
    ts TIMESTAMPTZ NOT NULL,
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    volume BIGINT,
    PRIMARY KEY (symbol, ts)
);"""

CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_symbol_ts ON price_data (symbol, ts DESC);"


def expand_to_seconds(symbol: str, df: pd.DataFrame) -> list[tuple]:
    """Expand each 1-minute bar into 60 second-level rows."""
    rows = []
    for _, bar in df.iterrows():
        ts_minute = bar["Datetime"]
        o, h, l, c = float(bar["Open"]), float(bar["High"]), float(bar["Low"]), float(bar["Close"])
        vol_per_sec = max(1, int(bar["Volume"]) // 60)
        # Linear interpolation open→close with small noise
        prices = np.linspace(o, c, 60) + np.random.normal(0, abs(c - o) * 0.05 + o * 0.0002, 60)
        prices = np.clip(prices, l, h)  # keep within bar's high/low
        for sec in range(60):
            ts_sec = ts_minute + timedelta(seconds=sec)
            p = round(float(prices[sec]), 4)
            rows.append((symbol, ts_sec, p, p, p, p, vol_per_sec))
    return rows


async def fetch_symbol(conn, symbol: str, display_name: str) -> int:
    yf_ticker = YF_SYMBOL_MAP.get(symbol, symbol)
    try:
        ticker = yf.Ticker(yf_ticker)
        df = ticker.history(period="5d", interval="1m")
        if df.empty:
            print(f"  {symbol}: no data returned from yfinance")
            return 0
        df = df.reset_index()
        # Normalise column name: yfinance returns "Datetime" for intraday
        if "Datetime" not in df.columns and "Date" in df.columns:
            df = df.rename(columns={"Date": "Datetime"})
        df["Datetime"] = pd.to_datetime(df["Datetime"]).dt.tz_convert("UTC")
        rows = expand_to_seconds(symbol, df)
        if rows:
            await conn.executemany(
                "INSERT INTO price_data VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT DO NOTHING",
                rows,
            )
        print(f"  {symbol}: {len(df)} minute bars → {len(rows)} second rows")
        return len(rows)
    except Exception as e:
        print(f"  {symbol}: ERROR — {e}")
        return 0


async def main():
    conn = await asyncpg.connect(os.getenv("SUPABASE_DB_URL"), ssl="require")

    # Recreate price/stock tables (preserves auth tables)
    await conn.execute("DROP TABLE IF EXISTS price_data CASCADE")
    await conn.execute("DROP TABLE IF EXISTS stocks CASCADE")
    await conn.execute(CREATE_STOCKS)
    await conn.execute(CREATE_PRICE)
    await conn.execute(CREATE_INDEX)

    # Insert stock metadata
    await conn.executemany(
        "INSERT INTO stocks VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING",
        INSTRUMENTS,
    )
    print(f"Inserted {len(INSTRUMENTS)} stocks.\nFetching 1-minute data from yfinance...\n")

    total_rows = 0
    for sym, name, *_ in INSTRUMENTS:
        total_rows += await fetch_symbol(conn, sym, name)

    await conn.close()
    print(f"\nDone — {total_rows:,} total second-level rows across {len(INSTRUMENTS)} instruments.")


if __name__ == "__main__":
    asyncio.run(main())
