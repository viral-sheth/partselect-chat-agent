# PartSelect AI Chat Agent

An AI-powered chat assistant for PartSelect, an appliance parts e-commerce platform. Built as a full-stack agentic application that helps customers find refrigerator and dishwasher parts, check compatibility, get installation guidance, manage a cart, and track orders.

**Live Demo:** https://partselect-chat-agent.vercel.app  
**Backend API:** https://partselect-chat-agent-production.up.railway.app/health  
**Demo Videos:** https://loom.com/share/folder/3f75ade7c8464ba8b8ab8b60469ddf59

---

## What It Does

Users can have a natural conversation to:
- **Search for parts** — "I need a water filter for my Whirlpool fridge"
- **Check compatibility** — "Is part PS11752778 compatible with model WDT780SAEM1?"
- **Get installation help** — "How do I install a dishwasher door latch?"
- **Troubleshoot problems** — "My ice maker stopped working"
- **Manage cart** — "Add that to my cart" / "Show me my cart"
- **Track orders** — "Where is my order #12345?"

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                           │
│                                                                     │
│   ┌──────────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│   │  ChatWindow  │    │  MessageBubble   │    │   Rich Cards    │  │
│   │  InputBar    │    │  (Markdown)      │    │  ProductCard    │  │
│   │  CartPanel   │    │  SSE stream      │    │  CompatCard     │  │
│   └──────┬───────┘    └──────────────────┘    │  InstallCard    │  │
│          │  usePartSelectChat.ts (Zustand)     └─────────────────┘  │
└──────────┼──────────────────────────────────────────────────────────┘
           │  POST /v1/chat   (SSE stream)
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Railway)                           │
│                                                                     │
│   FastAPI ──► Agent Loop (loop.py)                                  │
│                    │                                                │
│                    ▼                                                │
│            Groq API  ◄──────────────────────────────────┐          │
│         (Llama 4 Scout)                                 │          │
│                    │  tool_calls[]                       │          │
│                    ▼                                     │          │
│   ┌────────────────────────────────────────────────┐    │          │
│   │               Tool Registry                    │    │          │
│   │                                                │    │          │
│   │  search_products ──► ChromaDB (vector search)  │    │          │
│   │  check_compatibility ──► SQLite                │    │          │
│   │  get_installation_guide ──► dynamic generator  │    │          │
│   │  get_troubleshooting ──► SQLite                │    │          │
│   │  add_to_cart / get_cart ──► SQLite             │    │          │
│   │  get_order_status ──► SQLite                   │    │          │
│   └────────────────────┬───────────────────────────┘    │          │
│                        │  tool results                   │          │
│                        └─────────────────────────────────┘          │
│                                                                     │
│   ┌─────────────────────┐    ┌──────────────────────────────────┐  │
│   │  ChromaDB           │    │  SQLite (SQLAlchemy async)        │  │
│   │  73 parts embedded  │    │  products, cart, orders,          │  │
│   │  all-MiniLM-L6-v2   │    │  compatibility, sessions          │  │
│   └─────────────────────┘    └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## How the System Works — Request Flow

Here is the end-to-end journey of a single user message through the system:

```
User types: "My dishwasher is not draining"
```

**1. Frontend captures the message**
- `usePartSelectChat.ts` appends the message optimistically to the UI
- Opens a `fetch()` SSE stream to `POST /v1/chat` with `{ message, session_id }`

**2. FastAPI receives the request**
- `chat.py` loads the session's conversation history from SQLite
- Passes the full history + new message to the Agent Loop

**3. Agent Loop builds the LLM context**
- `loop.py` constructs: `[system_prompt] + [conversation history] + [new user message]`
- Attaches all 7 tool definitions in OpenAI function-calling format
- Sends to Groq (Llama 4 Scout) via async API call

**4. LLM decides to call a tool**
- Groq returns `tool_calls: [{ name: "get_troubleshooting", args: { issue: "dishwasher not draining", ... } }]`
- The loop emits `{"type": "tool_start", "tool": "get_troubleshooting"}` over SSE

**5. Tool executes**
- `get_troubleshooting` queries SQLite for matching symptoms, returns step-by-step diagnosis
- Result is simplified to plain text (`_simplify_for_groq`) before feeding back to the LLM

**6. LLM generates the final response**
- The simplified tool result is appended to the message context as a `role: tool` message
- Groq produces a natural-language reply with numbered steps
- The loop emits `{"type": "text", "content": "..."}` chunks over SSE as they arrive

**7. Done event closes the turn**
- Loop emits `{"type": "done", "final_messages": [...]}` 
- `chat.py` saves the updated conversation history back to SQLite

**8. Frontend renders the result**
- `MessageBubble` receives streamed text and renders it through the inline Markdown parser
- Bold, lists, numbered steps render natively — no external library needed
- For product/compatibility/installation tools, the matching rich card component mounts automatically

```
Total latency: ~600–900ms to first token, ~2s for a full tool-call round trip
```

### Tools Available to the LLM

| Tool | What it does |
|------|-------------|
| `search_products` | Semantic vector search across 73 real parts |
| `check_compatibility` | Verifies part ↔ model compatibility |
| `get_installation_guide` | Step-by-step installation instructions |
| `get_troubleshooting` | Diagnoses appliance problems |
| `add_to_cart` | Adds parts to session cart |
| `get_cart` | Returns current cart contents |
| `get_order_status` | Looks up order by number + email |

---

## Tech Stack

**Frontend**
- Next.js 16 (App Router) + TypeScript
- Tailwind CSS
- Server-Sent Events for streaming
- Custom markdown renderer (no external lib)

**Backend**
- FastAPI + Python 3.11
- Groq API (Llama 4 Scout 17B) for LLM + intent classification
- ChromaDB for vector similarity search
- SentenceTransformers (`all-MiniLM-L6-v2`) for embeddings
- SQLite + SQLAlchemy (async) for persistence
- Docker on Railway

**Data**
- 73 real parts scraped from PartSelect using Playwright
- 145 compatibility rows across 20 appliance models (10 dishwasher, 10 refrigerator)
- Real prices, descriptions, stock status, and product images
- Auto-seeded into SQLite + ChromaDB on first startup

---

## Real Data — Not Fake Seeds

The scraper (`scraper/scrape_partselect.py`) uses Playwright to scrape live data from PartSelect:

1. For each of 20 model numbers → fetch `/Models/{model}/Parts/` to get all part URLs
2. For each part URL → scrape name, price, stock, description, symptom tags
3. Compatibility inferred from which model pages each part appeared on
4. CDN image URLs constructed from part URL pattern (no lazy-loading needed)
5. All 73 parts saved to `scraper/scraped_parts.json` and committed to the repo

---

## Project Structure

```
├── backend/
│   ├── agent/
│   │   ├── loop.py             # Agentic tool-calling loop with SSE streaming
│   │   ├── system_prompt.py    # LLM instructions and rules
│   │   └── tools/              # 7 tool implementations
│   ├── api/
│   │   ├── chat.py             # POST /v1/chat → SSE stream
│   │   └── cart.py             # Cart REST endpoints
│   ├── db/
│   │   ├── chroma_client.py    # ChromaDB + embedding model
│   │   ├── database.py         # SQLAlchemy async engine
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── seed.py             # Auto-seeder from scraped_parts.json
│   │   └── session_store.py    # Conversation history (SQLite)
│   ├── data/
│   │   └── scraped_parts.json  # 73 real parts
│   ├── Dockerfile
│   ├── railway.toml
│   └── requirements.txt
├── frontend/
│   └── app/
│       ├── components/
│       │   ├── cards/          # ProductCard, CompatibilityCard, etc.
│       │   ├── cart/           # CartPanel slide-in drawer
│       │   └── chat/           # ChatWindow, MessageBubble, InputBar
│       ├── hooks/
│       │   └── usePartSelectChat.ts  # SSE streaming + state management
│       └── types/
└── scraper/
    └── scrape_partselect.py    # Playwright scraper
```

---

## Running Locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
# create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

## Key Technical Decisions

**Why ChromaDB + SQLite instead of a hosted vector DB?**  
Zero cost, no external dependencies, and 73 parts fits comfortably in memory. ChromaDB persists to disk via a Railway volume.

**Why Groq (Llama 4 Scout)?**  
~500ms response latency, free tier generous enough for demos, and function calling support. The same Groq client handles both the intent guard and the agent loop.

**Why SSE instead of WebSockets?**  
SSE is unidirectional and perfectly suited for streaming LLM output. Simpler to implement, works through proxies, and Next.js handles it natively.

**Why a custom markdown renderer?**  
Avoids adding `react-markdown` + `remark-gfm` as dependencies. The LLM only produces bold, italic, code, and lists — a 60-line inline renderer handles all of it.
