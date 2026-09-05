# Mail Assistant

Privacy-first AI email assistant. It connects to Gmail, suggests replies and prioritises
the inbox, and runs its language model locally by default so email content never leaves
the machine. Email bodies are never written to disk; the database stores only metadata
(message id, category, score, provider, model).

It is also the practical component of a B.Sc. thesis at HAW Hamburg, which asks whether a
locally-hosted 8B model can do this as well as a cloud API. The same application is wired
to two interchangeable backends, Llama 3.1 8B via Ollama and Anthropic Claude, and the
scripts in `evaluation/` compare them on both tasks. Neither study found a statistically
significant difference between the two.

## Stack

FastAPI (Python 3.12) backend, Next.js frontend, PostgreSQL 16 in Docker, Ollama for the
local model, Gmail API with OAuth 2.0.

## Prerequisites

- Python 3.12, Node.js 20+, Docker Desktop, [Ollama](https://ollama.com)
- A Google Cloud project with the Gmail API enabled and an OAuth 2.0 client of type "Web
  application", with `http://localhost:8000/auth/callback` as an authorised redirect URI.
  While the consent screen is in testing mode, add your own account under "Test users".
- An Anthropic API key, only if you want to use the cloud provider.

## Running it

**1. Configuration.** Copy the example file and fill in `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET` (and `ANTHROPIC_API_KEY`, if needed). The other defaults work as
they are. `.env` belongs at the repository root, not in `backend/`.

```bash
cp .env.example .env
echo "NEXT_PUBLIC_BACKEND_API=http://localhost:8000" > frontend/.env.local
```

**2. Database.** Docker Desktop has to be running first.

```bash
make up
```

**3. Local model,** in its own terminal:

```bash
ollama pull llama3.1:8b
ollama serve
```

**4. Backend,** in another terminal. Tables are created at startup, so there is no
migration step, but Postgres must already be up.

```bash
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
make install
make dev
```

`curl localhost:8000/health` should return `{"status":"ok"}`. API docs at
<http://localhost:8000/docs>.

**5. Frontend,** in a third terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000> and press "Login with Gmail".

## Other make targets

```bash
make down    # stop PostgreSQL
make logs    # follow container logs
make shell   # psql inside the container
```
