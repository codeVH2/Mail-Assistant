# Mail Assistant — Privacy-First AI Email Assistant

This is a bachelor thesis project investigating whether locally-hosted LLMs can match cloud APIs in quality for email assistance tasks, while preserving user privacy by design.

## Thesis context

**Research question:** Can locally-hosted LLMs (~7-8B parameters) deliver email assistance of comparable quality to cloud APIs, while preserving user privacy by design?

**Submission deadline:** End of July 2026.

**Two core features:**
1. AI-generated reply suggestions
2. Topic-based inbox prioritisation (categorisation + relevance scoring)

## Architecture

Monorepo with three main areas:
- `backend/` — FastAPI (Python 3.12) — handles auth, AI orchestration, business logic
- `frontend/` — Next.js (React + JavaScript) — user interface
- `evaluation/` — Python scripts for the comparative study (Capítulo 5 of thesis)

Key architectural principles:
- **Email content is never persisted to disk.** Processed in memory only.
- **Database stores only metadata:** opaque Gmail message IDs, classification labels, evaluation logs. No subject, body, sender, or recipient.
- **AI provider interface:** unified abstraction with two implementations — `LocalProvider` (Ollama) and `CloudProvider` (Anthropic). Same code path, different config.
- **Stateless by design:** Gmail is the source of truth; we only cache metadata.

## Technology stack

- **Backend:** FastAPI, Python 3.12, SQLAlchemy, Pydantic
- **Frontend:** Next.js (App Router), React, JavaScript (no TypeScript), Tailwind CSS
- **Database:** PostgreSQL 16 (via Docker)
- **Local AI:** Ollama with `llama3.1:8b`
- **Cloud AI:** Anthropic Claude API (for comparison only)
- **Email:** Gmail API with OAuth 2.0
- **Container runtime:** Docker Compose for development

## Coding conventions

- **Python:** type hints everywhere, Pydantic for data validation, async where it matters
- **JavaScript:** plain JS (no TS), functional React components with hooks, Tailwind for styling
- **Naming:** `snake_case` in Python, `camelCase` in JS, `kebab-case` for filenames in frontend
- **Tests:** pytest for backend; not strictly required for thesis but appreciated
- **Commits:** small, frequent, conventional commit format (`feat:`, `fix:`, `docs:`, etc.)
- **Comments:** explain *why*, not *what*. Code should be self-explanatory.

## Important constraints

- **Privacy is non-negotiable.** Never suggest persisting email content. If a feature requires it, flag the trade-off explicitly.
- **Hardware target:** runs on a MacBook Air M5 with 24 GB RAM. Local model is `llama3.1:8b`. Don't suggest larger models unless explicitly asked.
- **Scope is tight.** This is a bachelor thesis with ~14 weeks. Avoid scope creep — if a feature isn't directly serving the two core use cases or the comparative evaluation, it's out.
- **GDPR awareness:** mention GDPR implications when relevant (data minimisation, right to deletion, encrypted secrets).

## Communication preferences

- I'm a CS student, comfortable with Python, JavaScript, basic distributed systems. Less experienced with React, OAuth, ML evaluation methodologies.
- Explain trade-offs, not just solutions. I want to understand the *why* for the thesis defence.
- Push back on bad ideas — don't just agree. The thesis quality depends on rigorous thinking.
- I work in Portuguese, German, and English depending on context. Code and comments in English.

## Environment setup (already done)

- **Ollama** installed via Homebrew, `llama3.1:8b` pulled, server runs with `ollama serve`
- **Docker Desktop** installed; PostgreSQL 16 + Adminer run with `make up`
- **Python 3.12** used (3.14 is too new — many packages lack wheels for it)
- **venv** at `backend/.venv` — activate with `source backend/.venv/bin/activate`
- **psycopg driver:** using `psycopg[binary]==3.2.13` (psycopg3, not psycopg2) — requires `postgresql+psycopg://` prefix in DATABASE_URL
- **`GET /health`** tested and working: returns `{"status":"ok","ai_provider":"local"}`

## To run locally

```bash
# 1. Start PostgreSQL
make up

# 2. Start Ollama (keep this terminal open)
ollama serve

# 3. Start FastAPI (in backend/ with venv active)
cd backend && source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Current focus

**Phase 0 complete.** Moving to **Phase 1 — Backend core**.

Next steps:
1. Create Google Cloud credentials (OAuth 2.0) for Gmail API — done manually in console.cloud.google.com
2. Implement `backend/routers/auth.py` — Gmail OAuth flow (`/auth/gmail`, `/auth/callback`)
3. Implement `backend/routers/emails.py` — fetch emails + `/reply-suggest` endpoint
4. Wire routers into `main.py`

Router structure planned:
```
backend/routers/
├── auth.py      # GET /auth/gmail, GET /auth/callback
└── emails.py    # GET /emails, POST /reply-suggest, POST /prioritize
```
