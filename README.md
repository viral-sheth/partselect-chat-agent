# PartSelect AI Chat Agent

An AI-powered chat assistant for PartSelect, an appliance parts e-commerce platform. Built as a full-stack agentic application that helps customers find refrigerator and dishwasher parts, check compatibility, get installation guidance, manage a cart, and track orders.

**Live Demo:** https://partselect-chat-agent.vercel.app  
**Backend API:** https://partselect-chat-agent-production.up.railway.app/health

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
User → Next.js Frontend → FastAPI Backend → Groq (Llama 4 Scout)
                                         ↓
                              ChromaDB (semantic search)
                              SQLite (products, cart, orders)
                              SentenceTransformers (embeddings)
```

### How the Agent Works

1. User sends a message
2. **Intent Guard** classifies the message (Groq LLM) — blocks off-topic requests instantly
3. **Agent Loop** sends conversation history + 7 available tools to Llama 4 Scout
4. LLM decides to call a tool or respond directly
5. Tools execute (search ChromaDB, query SQLite, etc.) and results stream back
6. LLM generates a final response with structured data
7. Frontend renders tool results as rich cards (product cards, compatibility results, etc.)
8. Everything streams via **Server-Sent Events** in real time

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
│   │   ├── intent_guard.py     # Off-topic filter with LLM classification
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
