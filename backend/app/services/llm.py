import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# In-memory LLM config — switchable at runtime without restart
_llm_config: dict = {
    "provider": os.getenv("LLM_PROVIDER", "groq"),
    "model": os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
}


def update_llm_config(provider: str, model: str) -> None:
    _llm_config["provider"] = provider
    _llm_config["model"] = model


def get_llm_config() -> dict:
    return dict(_llm_config)


def _get_client() -> tuple[AsyncOpenAI, str]:
    provider = _llm_config["provider"]
    if provider == "openrouter":
        client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
        model = _llm_config.get("model", os.getenv("OPENROUTER_MODEL", "qwen/qwen3-8b"))
    elif provider == "xai":
        client = AsyncOpenAI(base_url="https://api.x.ai/v1", api_key=os.getenv("XAI_API_KEY"))
        model = _llm_config.get("model", "grok-3-mini-beta")
    elif provider == "groq":
        client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
        model = _llm_config.get("model", "llama-3.3-70b-versatile")
    else:
        client = AsyncOpenAI(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), api_key="ollama")
        model = _llm_config.get("model", os.getenv("OLLAMA_MODEL", "qwen3:8b"))
    return client, model


async def chat_completion(messages: list, temperature: float = 0.1) -> str:
    client, model = _get_client()
    resp = await client.chat.completions.create(model=model, messages=messages, temperature=temperature)
    raw = resp.choices[0].message.content.strip()
    # Strip <think>...</think> reasoning blocks (Qwen3, DeepSeek R1, etc.)
    import re
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


async def chat_completion_json(messages: list) -> dict:
    raw = await chat_completion(messages)
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])
