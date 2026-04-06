from fastapi import APIRouter
from ..models.request import LLMConfigRequest
from ..services.llm import update_llm_config, get_llm_config

router = APIRouter()

_AVAILABLE_MODELS = [
    {"provider": "groq", "model": "llama-3.3-70b-versatile",              "label": "Llama 3.3 70B (Groq)"},
    {"provider": "groq", "model": "qwen/qwen3-32b",                        "label": "Qwen3 32B (Groq)"},
    {"provider": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct", "label": "Llama 4 Scout 17B (Groq)"},
    {"provider": "groq", "model": "moonshotai/kimi-k2-instruct",           "label": "Kimi K2 (Groq)"},
    {"provider": "groq", "model": "llama-3.1-8b-instant",                  "label": "Llama 3.1 8B Fast (Groq)"},
    {"provider": "ollama", "model": "qwen3:8b",                            "label": "Qwen3 8B (Local)"},
    {"provider": "xai", "model": "grok-3-mini-beta",                       "label": "Grok 3 Mini (xAI)"},
    {"provider": "xai", "model": "grok-3-beta",                            "label": "Grok 3 (xAI)"},
    {"provider": "openrouter", "model": "anthropic/claude-3.5-haiku",      "label": "Claude 3.5 Haiku"},
    {"provider": "openrouter", "model": "openai/gpt-4o-mini",              "label": "GPT-4o Mini"},
]


@router.get("/config/llm")
async def get_llm():
    return {**get_llm_config(), "available_models": _AVAILABLE_MODELS}


@router.post("/config/llm")
async def set_llm(req: LLMConfigRequest):
    update_llm_config(req.provider, req.model)
    return {"provider": req.provider, "model": req.model, "status": "updated"}
