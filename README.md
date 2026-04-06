# Stock Market Analytics Platform

AI-powered stock analytics platform. Ask natural-language questions about 32 stocks and receive tabular answers with optional charts. Built with a 4-node LangGraph agentic pipeline, SSE streaming, JWT auth, and full chat history persistence.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS + Recharts |
| Backend | FastAPI + asyncpg (Python 3.12) |
| Agent | LangGraph 4-node pipeline with SSE streaming |
| LLM | Groq (qwen3-32b) — switchable at runtime via UI, no restart required |
| Database | Supabase (Postgres) — market data + users + chat history |
| Observability | LangSmith — full trace per query (nodes, LLM calls, timings) |
| Auth | JWT (HS256, 7-day expiry) |
| Containerisation | Docker Compose |

---

## Quick Start

```bash
git clone <repo>
cd MeshDefend

# Edit backend/.env — fill in SUPABASE_DB_URL, GROQ_API_KEY, JWT_SECRET, LANGCHAIN_API_KEY
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| LangSmith Traces | https://smith.langchain.com → project: meshdefend |

---

## Environment Variables (`backend/.env`)

```env
SUPABASE_DB_URL=postgresql://...
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
LLM_MODEL=qwen/qwen3-32b
JWT_SECRET=your-secret-here

# LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=meshdefend
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Optional: local Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OLLAMA_MODEL=qwen3:8b
```

---

## API Contracts

### POST /api/auth/signup
```json
// Request
{ "email": "user@example.com", "password": "secret123", "display_name": "Alice" }
// Response 200
{ "access_token": "<JWT>", "token_type": "bearer", "user": { "id": "<uuid>", "email": "...", "display_name": "Alice" } }
```

### POST /api/auth/login
```json
// Request
{ "email": "user@example.com", "password": "secret123" }
// Response 200
{ "access_token": "<JWT>", "token_type": "bearer", "user": { "id": "<uuid>", "email": "..." } }
// Error 401
{ "detail": "Invalid credentials" }
```

### POST /api/chat/stream  ← primary endpoint

**Headers:** `Authorization: Bearer <token>`

**Request**
```json
{ "query": "Show me AAPL closing prices for the last 30 days", "session_id": "optional-uuid" }
```

**Response** — `Content-Type: text/event-stream`:
```
data: {"event":"step","data":{"step":"symbol_resolution","status":"running","message":"Resolving symbols..."}}
data: {"event":"step","data":{"step":"symbol_resolution","status":"done","result":"AAPL"}}
data: {"event":"step","data":{"step":"sql_generation","status":"running","message":"Analyzing query..."}}
data: {"event":"step","data":{"step":"sql_generation","status":"done"}}
data: {"event":"step","data":{"step":"sql_execution","status":"running","message":"Querying database..."}}
data: {"event":"step","data":{"step":"sql_execution","status":"done"}}
data: {"event":"step","data":{"step":"insights","status":"running","message":"Generating insights..."}}
data: {"event":"step","data":{"step":"insights","status":"done"}}
data: {"event":"result","data":{"type":"table","data":{"columns":["Date","Symbol","Close"],"rows":[...]},"chart":null,"sql_used":"SELECT ...","intent_summary":"...","session_id":"<uuid>"}}
data: [DONE]
```

**When user explicitly requests a chart** (`type` becomes `"both"`):
```
data: {"event":"step","data":{"step":"chart_build","status":"running","message":"Building visualization..."}}
data: {"event":"step","data":{"step":"chart_build","status":"done"}}
data: {"event":"result","data":{"type":"both","data":{...},"chart":{"chart_type":"line","x_key":"Date","series":["Symbol","Close"]},...}}
```

**Error event:**
```
data: {"event":"error","data":{"message":"LLM rate limit exceeded"}}
```

### GET /api/chat/sessions
```json
{ "sessions": [{ "id": "<uuid>", "title": "Show AAPL...", "created_at": "...", "updated_at": "...", "message_count": 4 }] }
```

### GET /api/chat/sessions/{session_id}/messages
```json
{
  "messages": [
    { "id": "<uuid>", "role": "user", "content": "Show me AAPL today", "response_json": null, "created_at": "..." },
    { "id": "<uuid>", "role": "assistant", "content": "AAPL closed at...",
      "response_json": { "type": "table", "data": { "columns": [...], "rows": [...] }, "chart": null, "sql_used": "...", "intent_summary": "..." },
      "created_at": "..." }
  ]
}
```

Note: `response_json` is a full JSON object (not a string) — the frontend uses it directly to re-render DataTable and ChartView when loading history.

### GET /api/config/llm
```json
{
  "provider": "groq",
  "model": "qwen/qwen3-32b",
  "available_models": [
    {"provider":"groq","model":"qwen/qwen3-32b","label":"Qwen3 32B (Groq)"},
    {"provider":"groq","model":"llama-3.3-70b-versatile","label":"Llama 3.3 70B (Groq)"},
    {"provider":"ollama","model":"qwen3:8b","label":"Qwen3 8B (Local)"},
    {"provider":"xai","model":"grok-3-beta","label":"Grok 3 (xAI)"},
    {"provider":"openrouter","model":"anthropic/claude-3.5-haiku","label":"Claude 3.5 Haiku"}
  ]
}
```

### POST /api/config/llm
```json
// Request
{ "provider": "groq", "model": "llama-3.3-70b-versatile" }
// Response
{ "provider": "groq", "model": "llama-3.3-70b-versatile", "status": "updated" }
```
Change takes effect on the next chat query. No restart required.

---

## Data Setup

> **The Supabase database is already seeded.** If you are running the demo against the provided `SUPABASE_DB_URL` in `.env`, skip this section — data is live and queries will work immediately.
>
> Follow the steps below only if you are setting up your own Supabase instance or want to re-generate the dataset from scratch.

### Prerequisites

```bash
cd backend
pip install -r requirements.txt   # installs yfinance, asyncpg, pandas, numpy, python-dotenv
cp .env.example .env              # fill in your own SUPABASE_DB_URL
```

### Step 1 — Create the database schema

The schema is applied automatically when the FastAPI server starts (`app/db/migrations.py` runs on startup). Alternatively run:

```bash
python -c "import asyncio; from app.db.migrations import run_migrations; asyncio.run(run_migrations())"
```

This creates the `stocks`, `price_data`, `users`, `chat_sessions`, and `chat_messages` tables.

### Step 2 — Fetch real market data (second-level granularity)

```bash
python scripts/fetch_yfinance.py
```

**What it does:**
- Fetches the last 7 days of real 1-minute OHLCV bars from Yahoo Finance (via yfinance) for all 32 instruments
- Expands each 1-minute bar into 60 second-level rows — prices are linearly interpolated from the bar's open to close value, volume is divided evenly across the 60 seconds
- Inserts rows into `price_data` using `ON CONFLICT DO NOTHING` (safe to re-run)

**Expected output:** ~7M rows, covering the last 7 trading days at ~23,400 rows/day/stock.

**Note:** yfinance's finest available granularity is 1 minute (7-day lookback limit). The expansion to second-level rows satisfies the 60 data points per minute requirement while keeping prices anchored to real market values.

### Step 3 — Backfill YTD daily bars

```bash
python scripts/backfill_daily.py
```

**What it does:**
- Fetches daily (1d interval) OHLCV bars from yfinance for January 1 2026 to present for all 32 instruments
- Inserts with `ON CONFLICT DO NOTHING` — existing second-level rows from Step 2 are preserved
- Adds ~2,000 daily rows that extend coverage to the start of the year

**Why this is needed:** Without this step, queries like "Compare SPY and QQQ this year" or "Show me AAPL YTD" would only return the last 7 days of data. The backfilled daily rows give the SQL agent full year-to-date coverage.

**Expected output:** ~2,000 additional rows. Total database: ~7.5M rows spanning January 2026 to present.

### Full data pipeline (run in order)

```bash
cd backend
pip install -r requirements.txt
python scripts/fetch_yfinance.py      # ~5–10 min depending on rate limits
python scripts/backfill_daily.py      # ~1–2 min
```

No API key required — yfinance uses Yahoo Finance's public endpoints.

---

## Architecture

```
Browser (Next.js)
  │
  │  POST /api/chat/stream   Authorization: Bearer <JWT>
  ▼
FastAPI  ──→  JWT middleware  ──→  analytics.run_agent()
                                       │
                                       ▼
                             LangGraph pipeline (astream)
                             ┌─────────────────────────┐
                             │  Node 1: resolve_symbols │  LLM: name → ticker
                             │  Node 2: generate_sql    │  LLM: intent + SQL
                             │  Node 3: execute_sql     │  asyncpg → Supabase
                             │  Node 4: build_response  │  chart (opt-in only)
                             └─────────────────────────┘
                                       │ SSE events per node
                                       ▼
                             text/event-stream → ReadableStream
                             ├─ step events  → live progress UI
                             └─ result event → DataTable + optional ChartView

                          All traces → LangSmith (project: meshdefend)
```

---

## API

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/signup` | Create account → JWT |
| POST | `/api/auth/login` | Login → JWT |
| GET | `/api/auth/me` | Validate token |

### Chat (requires `Authorization: Bearer <token>`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat/stream` | NL query → SSE stream of step events + result |
| GET | `/api/chat/sessions` | List user's chat sessions |
| GET | `/api/chat/sessions/{id}/messages` | Full message history (with response_json for table/chart re-render) |

### Config
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/config/llm` | Current provider/model + available models |
| POST | `/api/config/llm` | Switch provider/model at runtime |

### Stocks
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stocks` | All tracked stocks |
| GET | `/api/stocks/live` | Real-time quotes (yfinance) — used by ticker strip |
| GET | `/api/stocks/{symbol}/history` | OHLCV history |
| GET | `/health` | Health check |

### Example: Streaming chat query

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpass"}' \
  | jq -r .access_token)

curl -X POST http://localhost:8000/api/chat/stream \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the % change in AAPL over the last 7 days?"}'
```

### Example: Switch LLM at runtime (no restart)

```bash
curl -X POST http://localhost:8000/api/config/llm \
  -H "Content-Type: application/json" \
  -d '{"provider": "groq", "model": "llama-3.3-70b-versatile"}'
```

---

## LangGraph Pipeline

Four nodes, each ≤ 10 lines, each delegating to a single-purpose service:

```
START
  │
  ▼
resolve_symbols_node   — LLM maps "Apple" → AAPL, "Reliance" → RELIANCE.NS
  │                      Uses name→symbol map built from DB stocks table
  ▼
generate_sql_node      — LLM #1: classify intent (stocks, time range, metric, output_type)
  │                      LLM #2: write SQL from intent + schema
  ▼
execute_sql_node       — asyncpg executes SQL on Supabase; _pivot() for multi-symbol results
  │
  ▼
build_response_node    — generates analytical summary; builds chart config ONLY if
  │                      intent.output_type in ("chart", "both")
  ▼
END
```

**Table is the default. Charts are opt-in** — the system never generates a chart unless the user explicitly asks for one ("plot", "chart", "graph", "visual").

---

## LLM Switcher

Switch provider and model live via the UI dropdown (calls `POST /api/config/llm`) or via curl. No restart required. Available providers:

| Provider | Models |
|----------|--------|
| Groq | qwen/qwen3-32b, llama-3.3-70b-versatile, llama-4-scout-17b, llama-3.1-8b-instant |
| Ollama | qwen3:8b (local) |
| xAI | grok-3-beta, grok-3-mini-beta |
| OpenRouter | claude-3.5-haiku, gpt-4o-mini |

---

## Observability (LangSmith)

Every query is traced automatically. Visit https://smith.langchain.com → project **meshdefend** to see:
- Full LangGraph DAG with node timings
- LLM inputs/outputs for each of the 3–4 LLM calls per query
- Token counts and latency per step
- SQL generated and execution time

No code instrumentation required — tracing is enabled via `LANGCHAIN_TRACING_V2=true`.

---

## Sample Prompts

```
# Tabular (default)
"What is the closing price of AAPL today?"
"Compare AAPL and MSFT closing prices over the last 7 days"
"What is the % change in NVDA, AMD, and Intel over the last 30 days?"
"Show me the top 5 stocks by volume today"
"Compare SPY and QQQ this year"
"Show OHLCV for Tesla this week"
"Which stock had the highest percent gain today?"

# Chart (opt-in — must explicitly ask)
"Plot a line chart of AAPL closing prices this week"
"Show me a bar chart of the top 5 stocks by volume"
"Draw a multi-line chart comparing Apple, Microsoft, and Google this month"

# Symbol resolution (no need to know tickers)
"Show me Reliance and Infosys closing prices this week"
"Compare Apple, Tesla, and Nvidia this month"
```

---

## Project Structure

```
MeshDefend/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, router registration, DB migration on startup
│   │   ├── api/
│   │   │   ├── auth.py              # /api/auth/* endpoints
│   │   │   ├── chat.py              # /api/chat/stream + history endpoints
│   │   │   ├── config.py            # /api/config/llm GET+POST
│   │   │   └── stocks.py            # /api/stocks + live + history
│   │   ├── services/
│   │   │   ├── agent.py             # LangGraph 4-node graph
│   │   │   ├── analytics.py         # run_agent() — SSE generator, session/message persistence
│   │   │   ├── llm.py               # In-memory LLM config, chat_completion helpers
│   │   │   ├── auth.py              # JWT encode/decode, bcrypt helpers
│   │   │   ├── chart.py             # build_chart_config(), needs_chart()
│   │   │   └── live.py              # yfinance real-time quotes (ticker strip)
│   │   ├── prompts/
│   │   │   ├── symbol_resolution.py
│   │   │   ├── intent_classification.py
│   │   │   ├── sql_generation.py    # 10 full examples + CRITICAL RULES
│   │   │   └── analytics_summary.py
│   │   ├── db/
│   │   │   ├── client.py            # asyncpg pool with JSONB codec
│   │   │   ├── queries.py           # all DB calls
│   │   │   └── migrations.py        # CREATE TABLE users/sessions/messages
│   │   ├── middleware/auth.py       # JWT FastAPI dependency
│   │   └── models/
│   │       ├── request.py
│   │       └── response.py
│   ├── scripts/
│   │   ├── fetch_yfinance.py        # Fetch real 1-min data → expand to 60 rows/min
│   │   ├── backfill_daily.py        # Backfill YTD daily bars
│   │   └── generate_data.py         # Synthetic fallback (not needed if yfinance used)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── justifications.txt           # Architecture decision log
└── frontend/
    ├── app/
    │   ├── page.tsx                 # Auth guard, layout
    │   ├── login/page.tsx           # Login/signup
    │   ├── components/
    │   │   ├── Header.tsx           # LLM switcher, user avatar
    │   │   ├── Sidebar.tsx          # Chat history sessions
    │   │   ├── ChatInterface.tsx    # SSE consumer, history load
    │   │   ├── StreamingMessage.tsx # Live step-by-step progress
    │   │   ├── DataTable.tsx        # Tabular results
    │   │   ├── ChartView.tsx        # Recharts line/bar/pie
    │   │   ├── LLMSwitcher.tsx      # Provider/model dropdown
    │   │   └── TickerStrip.tsx      # Live price banner
    │   └── lib/
    │       ├── api.ts               # All fetch calls, streamChat generator
    │       ├── auth.ts              # Token storage helpers
    │       └── types.ts             # TypeScript interfaces
    └── Dockerfile
```
