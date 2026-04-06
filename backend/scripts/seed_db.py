"""Seed Supabase with synthetic data. Run after generate_data.py."""
import asyncio
import asyncpg
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")
DATA_DIR = Path(__file__).parent / "data"

CREATE_STOCKS = """CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(20) PRIMARY KEY, name VARCHAR(100) NOT NULL,
    sector VARCHAR(50), exchange VARCHAR(20) DEFAULT 'NASDAQ');"""

CREATE_PRICE = """CREATE TABLE IF NOT EXISTS price_data (
    symbol VARCHAR(20) REFERENCES stocks(symbol),
    ts TIMESTAMPTZ NOT NULL, open NUMERIC(12,4), high NUMERIC(12,4),
    low NUMERIC(12,4), close NUMERIC(12,4), volume BIGINT,
    PRIMARY KEY (symbol, ts));"""

CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_symbol_ts ON price_data (symbol, ts DESC);"


async def seed():
    conn = await asyncpg.connect(os.getenv("SUPABASE_DB_URL"), ssl="require")
    # Drop and recreate so schema changes (e.g. VARCHAR width) are always applied
    await conn.execute("DROP TABLE IF EXISTS price_data CASCADE")
    await conn.execute("DROP TABLE IF EXISTS stocks CASCADE")
    await conn.execute(CREATE_STOCKS)
    await conn.execute(CREATE_PRICE)
    await conn.execute(CREATE_INDEX)
    stocks_df = pd.read_csv(DATA_DIR / "stocks.csv")
    await conn.executemany("INSERT INTO stocks VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING",
                           stocks_df.values.tolist())
    for csv in DATA_DIR.glob("*.csv"):
        if csv.stem == "stocks":
            continue
        df = pd.read_csv(csv, parse_dates=["ts"])
        df["ts"] = df["ts"].dt.tz_localize("UTC")
        rows = [tuple(r) for r in df.itertuples(index=False)]
        await conn.executemany(
            "INSERT INTO price_data VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT DO NOTHING", rows)
        print(f"  Seeded {csv.stem}: {len(rows):,} rows")
    await conn.close()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
