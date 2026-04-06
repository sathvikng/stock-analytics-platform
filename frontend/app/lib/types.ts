export interface TableData {
  columns: string[];
  rows: (string | number | null)[][];
}

export interface ChartConfig {
  chart_type: "line" | "bar" | "pie";
  x_key: string;
  series: string[];
}

export interface ChatResponse {
  type: "table" | "chart" | "both" | "answer";
  data: TableData;
  chart?: ChartConfig;
  sql_used: string;
  intent_summary: string;
  session_id?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

export interface StockInfo {
  symbol: string;
  name: string;
  sector: string | null;
  exchange: string;
}

export interface LiveQuote {
  symbol: string;
  price: number;
  change: number;
  pct_change: number;
  volume: number;
  market_cap: number;
  as_of: string;
}

// ── Streaming ─────────────────────────────────────────────────────────────────

export interface StepData {
  step: string;
  status: "running" | "done";
  message?: string;
  result?: string;
}

export interface StreamEvent {
  event: "step" | "result" | "error";
  data: StepData | ChatResponse | { message: string };
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  display_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  response_json?: ChatResponse;
  created_at: string;
}

// ── LLM Config ────────────────────────────────────────────────────────────────

export interface LLMModel {
  provider: string;
  model: string;
  label: string;
}

export interface LLMConfig {
  provider: string;
  model: string;
  available_models: LLMModel[];
}
