# Builder Discovery Pipeline

AI-native tool to discover high-propensity founders **before** they self-identify. Scrapes GitHub for builder signals — activity dips at vesting cliffs, internal tools shipped publicly, AI-native building patterns — and scores them on a 6-dimension founder propensity model.

Built for an AI-native VC fund. Zero-cost MVP using free-tier APIs only.

## Architecture

```
backend/          Python FastAPI + SQLite (async)
  app/
    api/v1/       REST endpoints (people, pipeline, signals, dashboard, etc.)
    collectors/   GitHub GraphQL/REST scraper, Twitter stub
    llm/          Gemini 2.0 Flash integration for builder classification
    models/       SQLAlchemy ORM (Person, Repository, Signal, Organization, …)
    processors/   Activity analysis, repo quality scoring, internal-tool detection
    services/     Discovery, enrichment, scoring orchestration
    jobs/         Background task runner (cron-style)
  scripts/        CLI pipeline runner
  data/           SQLite database (auto-created, gitignored)

frontend/         Next.js 14 + Tailwind CSS dashboard
  src/
    app/          Pages: Dashboard, People, Pipeline, Signals, Organizations
    components/   Charts, tables, filters, score badges
    lib/          API client, types, utilities
```

## Prerequisites

| Tool | Version | How to install |
|------|---------|----------------|
| **Python** | 3.12+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **uv** (Python pkg mgr) | latest | `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **GitHub PAT** | — | [github.com/settings/tokens](https://github.com/settings/tokens) (free, `public_repo` scope) |
| **Gemini API Key** | — | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (free tier) |

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/amviftw/builder-discovery.git
cd builder-discovery
```

### 2. Set up environment variables

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and add your real keys:

```
GITHUB_TOKEN=ghp_your_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install backend dependencies

```bash
cd backend
uv sync          # creates .venv and installs all deps
```

> **Don't have `uv`?** Use pip instead:
> ```bash
> cd backend
> python -m venv .venv
> # Linux/Mac: source .venv/bin/activate
> # Windows:   .venv\Scripts\activate
> pip install -e .
> ```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

### 5. Start the backend

```bash
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> Without `uv`: activate the venv first, then `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

The API is live at **http://127.0.0.1:8000** — check **http://127.0.0.1:8000/health** and **http://127.0.0.1:8000/docs** (Swagger UI).

### 6. Start the frontend

In a **separate terminal**:

```bash
cd frontend
npm run dev
```

Dashboard is live at **http://localhost:3000**

### 7. Run the discovery pipeline

In a **third terminal**:

```bash
cd backend

# Discover builders from GitHub
uv run python scripts/run_discovery.py discover

# Enrich discovered profiles (pull full GitHub data)
uv run python scripts/run_discovery.py enrich

# Score profiles on 6-dimension founder propensity model
uv run python scripts/run_discovery.py score

# Classify builders with Gemini AI
uv run python scripts/run_discovery.py classify

# Or run all stages in one shot:
uv run python scripts/run_discovery.py full

# Check pipeline stats anytime:
uv run python scripts/run_discovery.py stats
```

## Docker (Zero-Install Option)

Run everything with Docker — no Python, no Node.js, no manual setup:

```bash
# 1. Clone and set up env
git clone https://github.com/amviftw/builder-discovery.git
cd builder-discovery
cp .env.example backend/.env
# Edit backend/.env with your API keys

# 2. Build and start
docker compose up --build

# 3. Open the dashboard
# http://localhost:3000
```

To run the discovery pipeline inside Docker:

```bash
docker compose exec backend python scripts/run_discovery.py full
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/people` | List builders (paginated, filterable) |
| GET | `/api/v1/people/{id}` | Builder detail with scores and signals |
| GET | `/api/v1/dashboard/overview` | Dashboard KPIs and pipeline stats |
| GET | `/api/v1/pipeline/stats` | Pipeline stage counts |
| POST | `/api/v1/pipeline/bulk-advance` | Move builders between stages |
| GET | `/api/v1/signals` | Signal feed (activity dips, tool releases, etc.) |
| GET | `/api/v1/signals/summary` | Signal type breakdown |
| POST | `/api/v1/discovery/trigger` | Trigger discovery run |
| GET | `/api/v1/organizations` | Tracked organizations |
| GET | `/api/v1/repositories` | Tracked repositories |
| GET | `/api/v1/export/csv` | Export builders as CSV |

Full interactive docs at **http://127.0.0.1:8000/docs**

## Scoring Model

Each builder is scored on 6 dimensions (0-1 scale):

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Technical | 0.20 | Stars, forks, languages, repo quality, CI/CD |
| Momentum | 0.20 | Commit frequency, contribution trends, streak |
| AI-Nativeness | 0.20 | AI/ML repos, LLM tools, model usage topics |
| Leadership | 0.15 | Followers, org memberships, PRs reviewed |
| Departure Signal | 0.15 | Activity dips at vesting cliffs, pattern breaks |
| Network Quality | 0.10 | Contributor overlap, org prestige |

**Founder Propensity Score** = weighted sum → mapped to fit categories:
- **Exceptional** (≥ 0.80) — actively building, strong signals
- **Strong** (0.60–0.79) — high potential, worth tracking
- **Moderate** (0.40–0.59) — some signals present
- **Low** (< 0.40) — unlikely near-term founder

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub PAT with `public_repo` scope |
| `GEMINI_API_KEY` | Yes (for classify) | Google Gemini API key (free tier) |
| `GITHUB_TOKEN_2..9` | No | Extra tokens for rate limit rotation |
| `DATABASE_URL` | No | SQLite URL (auto-created) |
| `BACKEND_HOST` | No | Default: `127.0.0.1` |
| `BACKEND_PORT` | No | Default: `8000` |
| `NEXT_PUBLIC_API_URL` | No | Default: `http://127.0.0.1:8000/api/v1` |

## Project Roadmap

- [x] GitHub discovery (user search, repo-based, org-based)
- [x] Profile enrichment via GraphQL + REST fallback
- [x] 6-dimension founder propensity scoring
- [x] Gemini AI builder classification
- [x] Activity dip detection (vesting cliff signals)
- [x] Internal tool detector
- [x] Next.js dashboard with pipeline management
- [ ] Twitter/X signal integration
- [ ] LinkedIn manual verification workflow
- [ ] Email outreach automation
- [ ] Webhook alerts for high-score discoveries
- [ ] Multi-user support

## License

MIT
