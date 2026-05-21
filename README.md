# Mail-Assistant

> Privacy-first AI email assistant. Self-hostable.
> Benchmarks locally-run LLMs against cloud APIs.

## Why?
Gmail's Smart Compose and similar assistants send your inbox content
to cloud LLMs. Mail-Assistant asks: can we get equivalent quality from
a model running entirely on your own hardware?

## What it does
- Suggests reply drafts for incoming emails
- Prioritizes inbox using LLM-based classification
- Benchmarks local (Llama 3.1 8B via Ollama) vs cloud (Anthropic Claude)

## Architecture

- FastAPI backend
- Next.js frontend
- PostgreSQL (metadata only — no email body persistence)
- Docker Compose orchestration
- Gmail OAuth 2.0


## Bachelor Thesis
Practical component of my B.Sc. thesis at HAW Hamburg.
Full write-up available July 2026.
