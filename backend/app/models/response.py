from pydantic import BaseModel
from typing import Any, Optional, List


class TableData(BaseModel):
    columns: List[str]
    rows: List[List[Any]]


class ChartConfig(BaseModel):
    chart_type: str
    x_key: str
    series: List[str]


class ChatResponse(BaseModel):
    type: str
    data: TableData
    chart: Optional[ChartConfig] = None
    sql_used: str
    intent_summary: str


class StockInfo(BaseModel):
    symbol: str
    name: str
    sector: Optional[str]
    exchange: str


class StocksResponse(BaseModel):
    stocks: List[StockInfo]


class PricePoint(BaseModel):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoryResponse(BaseModel):
    symbol: str
    interval: str
    data: List[PricePoint]



class LiveQuote(BaseModel):
    symbol: str
    price: float
    change: float
    pct_change: float
    volume: int
    market_cap: int
    as_of: str


class LiveQuotesResponse(BaseModel):
    quotes: List[LiveQuote]


class AuthUser(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class SessionInfo(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class SessionsResponse(BaseModel):
    sessions: List[SessionInfo]


class MessageInfo(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    response_json: Optional[Any] = None
    created_at: str


class MessagesResponse(BaseModel):
    messages: List[MessageInfo]
