from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class HistoryRequest(BaseModel):
    start_date: str
    end_date: str
    interval: str = "1d"


class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LLMConfigRequest(BaseModel):
    provider: str
    model: str
