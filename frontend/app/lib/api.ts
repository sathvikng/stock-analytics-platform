import { ChatResponse, LiveQuote, StockInfo, StreamEvent, AuthResponse, Session, ChatMessage, LLMConfig } from "./types";
import { getToken, clearToken } from "./auth";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers as Record<string, string> ?? {}) },
  });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Login failed: ${res.status}`);
  }
  return res.json();
}

export async function signup(email: string, password: string, displayName?: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Signup failed: ${res.status}`);
  }
  return res.json();
}

// ── Streaming chat ────────────────────────────────────────────────────────────

export async function* streamChat(query: string, sessionId?: string): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(`API error: ${res.status}`);

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.startsWith("data: ") && line.trim() !== "data: [DONE]") {
        try { yield JSON.parse(line.slice(6)); } catch { /* skip malformed */ }
      }
    }
  }
}

// ── Sessions / history ────────────────────────────────────────────────────────

export async function getSessions(): Promise<Session[]> {
  const res = await authFetch("/api/chat/sessions");
  const data = await res.json();
  return data.sessions;
}

export async function getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  const res = await authFetch(`/api/chat/sessions/${sessionId}/messages`);
  const data = await res.json();
  return data.messages;
}

// ── LLM config ────────────────────────────────────────────────────────────────

export async function getLLMConfig(): Promise<LLMConfig> {
  const res = await fetch(`${BASE}/api/config/llm`);
  if (!res.ok) throw new Error("Failed to get LLM config");
  return res.json();
}

export async function setLLMConfig(provider: string, model: string): Promise<void> {
  const res = await fetch(`${BASE}/api/config/llm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, model }),
  });
  if (!res.ok) throw new Error("Failed to set LLM config");
}

// ── Stocks ────────────────────────────────────────────────────────────────────

export async function fetchLiveQuotes(symbols: string[]): Promise<LiveQuote[]> {
  const res = await fetch(`${BASE}/api/stocks/live?symbols=${symbols.join(",")}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  return data.quotes;
}

export async function fetchStocks(): Promise<StockInfo[]> {
  const res = await fetch(`${BASE}/api/stocks`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json();
  return data.stocks;
}

