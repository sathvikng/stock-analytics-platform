"""Generate synthetic OHLCV data.

Default (demo): all instruments × 50 daily candles.
To scale up, increase ROWS_PER_STOCK or change INTERVAL.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# ── Instruments ───────────────────────────────────────────────────────────────
# (symbol, display_name, sector, exchange)
INSTRUMENTS = [
    # US equities
    ("AAPL",         "Apple Inc.",              "Technology",        "NASDAQ"),
    ("GOOGL",        "Alphabet Inc.",            "Technology",        "NASDAQ"),
    ("MSFT",         "Microsoft Corp.",          "Technology",        "NASDAQ"),
    ("AMZN",         "Amazon.com Inc.",          "Consumer Cyclical", "NASDAQ"),
    ("TSLA",         "Tesla Inc.",               "Consumer Cyclical", "NASDAQ"),
    ("META",         "Meta Platforms",           "Technology",        "NASDAQ"),
    ("NVDA",         "NVIDIA Corp.",             "Technology",        "NASDAQ"),
    ("NFLX",         "Netflix Inc.",             "Communication",     "NASDAQ"),
    ("AMD",          "Advanced Micro Devices",   "Technology",        "NASDAQ"),
    ("INTC",         "Intel Corp.",              "Technology",        "NASDAQ"),
    ("PYPL",         "PayPal Holdings",          "Financial",         "NASDAQ"),
    ("SHOP",         "Shopify Inc.",             "Technology",        "NYSE"),
    ("CRM",          "Salesforce Inc.",          "Technology",        "NYSE"),
    ("ORCL",         "Oracle Corp.",             "Technology",        "NYSE"),
    ("IBM",          "IBM Corp.",                "Technology",        "NYSE"),
    # Commodities (ETFs — no special chars, liquid, yfinance-native)
    ("GLD",          "SPDR Gold Shares",         "Commodity",         "NYSE Arca"),
    ("SLV",          "iShares Silver Trust",     "Commodity",         "NYSE Arca"),
    # US Index ETFs
    ("SPY",          "S&P 500 ETF (SPY)",        "Index",             "NYSE Arca"),
    ("QQQ",          "NASDAQ 100 ETF (QQQ)",     "Index",             "NASDAQ"),
    ("DIA",          "Dow Jones ETF (DIA)",      "Index",             "NYSE Arca"),
    # Indian Indexes (mapped to ^NSEI / ^BSESN in live.py)
    ("NIFTY50",      "Nifty 50 Index",           "Index",             "NSE"),
    ("SENSEX",       "BSE Sensex",               "Index",             "BSE"),
    # Indian equities (NSE, .NS suffix = yfinance format)
    ("RELIANCE.NS",  "Reliance Industries",      "Energy",            "NSE"),
    ("TCS.NS",       "Tata Consultancy Services","Technology",        "NSE"),
    ("INFY.NS",      "Infosys Ltd.",             "Technology",        "NSE"),
    ("HDFCBANK.NS",  "HDFC Bank",                "Financial",         "NSE"),
    ("ICICIBANK.NS", "ICICI Bank",               "Financial",         "NSE"),
    ("WIPRO.NS",     "Wipro Ltd.",               "Technology",        "NSE"),
    ("HCLTECH.NS",   "HCL Technologies",         "Technology",        "NSE"),
    ("BAJFINANCE.NS","Bajaj Finance",             "Financial",         "NSE"),
    ("KOTAKBANK.NS", "Kotak Mahindra Bank",      "Financial",         "NSE"),
    ("LT.NS",        "Larsen & Toubro",          "Industrials",       "NSE"),
]

BASE_PRICES = {
    # US equities (USD)
    "AAPL": 185, "GOOGL": 140, "MSFT": 415, "AMZN": 185, "TSLA": 245,
    "META": 510, "NVDA": 850, "NFLX": 680, "AMD": 165, "INTC": 22,
    "PYPL": 62,  "SHOP": 88,  "CRM": 290,  "ORCL": 132, "IBM": 195,
    # Commodities ETFs (USD)
    "GLD": 295, "SLV": 32,
    # Index ETFs (USD)
    "SPY": 565, "QQQ": 455, "DIA": 432,
    # Indian indexes (index points)
    "NIFTY50": 23500, "SENSEX": 77500,
    # Indian equities (INR)
    "RELIANCE.NS": 2850, "TCS.NS": 3700,   "INFY.NS": 1500,
    "HDFCBANK.NS": 1750, "ICICIBANK.NS": 1300, "WIPRO.NS": 490,
    "HCLTECH.NS": 1800,  "BAJFINANCE.NS": 7000, "KOTAKBANK.NS": 2050,
    "LT.NS": 3600,
}

# ── Tune these to scale up ────────────────────────────────────────────────────
ROWS_PER_STOCK = 70           # daily candles per instrument (covers ~Jan–Apr 2026)
INTERVAL = timedelta(days=1)  # change to timedelta(minutes=1) etc. to scale
# ─────────────────────────────────────────────────────────────────────────────


def generate_instrument(symbol: str, start_date: datetime) -> pd.DataFrame:
    price = BASE_PRICES[symbol]
    records, ts = [], start_date
    for _ in range(ROWS_PER_STOCK):
        while ts.weekday() >= 5:
            ts += INTERVAL
        price *= 1 + np.random.normal(0, 0.012)
        noise = abs(np.random.normal(0, price * 0.004))
        records.append((
            symbol, ts,
            round(price - noise / 2, 4),
            round(price + noise, 4),
            round(price - noise, 4),
            round(price, 4),
            int(np.random.randint(500_000, 5_000_000)),
        ))
        ts += INTERVAL
    return pd.DataFrame(records, columns=["symbol", "ts", "open", "high", "low", "close", "volume"])


def main():
    out = Path(__file__).parent / "data"
    out.mkdir(exist_ok=True)
    start = datetime(2026, 1, 2, 13, 30)
    for sym, *_ in INSTRUMENTS:
        df = generate_instrument(sym, start)
        # Safe filename: replace characters invalid on some filesystems
        fname = sym.replace(".", "_").replace("^", "_")
        df.to_csv(out / f"{fname}.csv", index=False)
        print(f"  {sym}: {len(df)} rows")
    pd.DataFrame(INSTRUMENTS, columns=["symbol", "name", "sector", "exchange"]).to_csv(
        out / "stocks.csv", index=False
    )
    total = len(INSTRUMENTS) * ROWS_PER_STOCK
    print(f"Done — {total} rows across {len(INSTRUMENTS)} instruments.")


if __name__ == "__main__":
    main()
