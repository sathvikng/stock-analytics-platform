import asyncio
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from ..models.response import StocksResponse, HistoryResponse, PricePoint, LiveQuote, LiveQuotesResponse
from ..db.queries import get_all_stocks, get_stock_history
from ..services.live import get_quote, get_intraday

router = APIRouter()


@router.get("/stocks", response_model=StocksResponse)
async def list_stocks():
    stocks = await get_all_stocks()
    return StocksResponse(stocks=stocks)


@router.get("/stocks/live", response_model=LiveQuotesResponse)
async def live_quotes(symbols: str = Query(..., description="Comma-separated tickers, e.g. AAPL,MSFT")):
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    quotes = await asyncio.gather(*[asyncio.to_thread(get_quote, s) for s in syms])
    return LiveQuotesResponse(quotes=[LiveQuote(**q) for q in quotes])


@router.get("/stocks/{symbol}/quote", response_model=LiveQuote)
async def single_quote(symbol: str):
    data = await asyncio.to_thread(get_quote, symbol.upper())
    return LiveQuote(**data)


@router.get("/stocks/{symbol}/intraday")
async def intraday(symbol: str, period: str = Query("1d"), interval: str = Query("1m")):
    data = await asyncio.to_thread(get_intraday, symbol.upper(), period, interval)
    if not data:
        raise HTTPException(status_code=404, detail="No intraday data found")
    return {"symbol": symbol.upper(), "period": period, "interval": interval, "data": data}


@router.get("/stocks/{symbol}/history", response_model=HistoryResponse)
async def stock_history(
    symbol: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    interval: str = Query("1d"),
):
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    rows = await get_stock_history(symbol, start_dt, end_dt)
    data = [PricePoint(ts=str(r["ts"]), open=float(r["open"]), high=float(r["high"]),
                       low=float(r["low"]), close=float(r["close"]), volume=int(r["volume"])) for r in rows]
    return HistoryResponse(symbol=symbol, interval=interval, data=data)
