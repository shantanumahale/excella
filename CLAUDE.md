# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**Excella** is a full-stack financial data platform and equity screener. It ingests fundamentals from SEC EDGAR, macroeconomic data from FRED, and pricing data from yFinance, computes 142+ derived financial metrics and intrinsic value estimates via a built-in valuation engine, and serves them through a REST API and interactive Next.js frontend.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, PostgreSQL + TimescaleDB, Redis, RabbitMQ, Elasticsearch, MinIO
- **Frontend:** Next.js 16, React 19, Tailwind CSS v4, TanStack Table/Query, TypeScript
- **Infrastructure:** Docker Compose (9 services), APScheduler for CRON tasks

## Running the Project

```bash
# Start all services
docker compose up -d

# Backend only
docker compose up api -d

# Frontend only
cd frontend && npm run dev

# Run backend tests
docker compose exec api pytest --cov=app --cov-report=term-missing

# Run frontend tests
cd frontend && npm test

# Type check frontend
cd frontend && npx tsc --noEmit
```

## Project Structure

```
src/                          # Backend (Python/FastAPI)
  app/
    main.py                   # FastAPI entry point
    config.py                 # Settings
    worker.py                 # RabbitMQ consumer
    scheduler.py              # CRON scheduler
    api/                      # REST endpoints (17 routes)
    db/                       # ORM models + session
    ingestion/                # EDGAR, FRED, yFinance workers
    pipeline/                 # Data processing (XBRL mapper, normalizer, validator)
    metrics/                  # 12 metric computation modules
    valuation/                # Intrinsic value engine (DCF, DDM, Comps, Residual Income)
    queue/                    # RabbitMQ broker
frontend/                     # Frontend (Next.js/React/TS)
  src/
    app/                      # Routes: screener, company (+ valuation), compare, macro, watchlist, auth
    components/               # UI components
    hooks/                    # Data fetching hooks
    lib/                      # API client, types, formatters
    providers/                # React Query, Theme, Auth
```

## Development Workflow

Follow this pipeline for all feature work:

1. **Plan** - Use `/plan` to create implementation plan before coding
2. **TDD** - Use `/tdd` to write tests first (RED -> GREEN -> REFACTOR)
3. **Review** - Use `/code-review` after writing code
4. **Fix** - Use `/build-fix` if build/type errors occur

## Code Quality Rules

### General
- Functions < 50 lines, files < 800 lines (200-400 typical)
- No deep nesting (> 4 levels) - use early returns
- Immutability: return new objects, never mutate existing ones
- No hardcoded values - use constants, config, or env vars
- Handle errors explicitly at every level - never silently swallow errors
- Validate all input at system boundaries (API endpoints, external data)

### Python (Backend)
- Type hints on all public functions
- Use context managers (`with`) for resource management
- Parameterized SQL queries only - never f-strings in queries
- Use `logging` not `print()`
- Catch specific exceptions, never bare `except:`
- Use list comprehensions over C-style loops
- No mutable default arguments (`def f(x=[])` -> `def f(x=None)`)
- No blocking calls in async endpoints
- Use Pydantic models for request/response validation

### TypeScript (Frontend)
- Complete `useEffect`/`useMemo`/`useCallback` dependency arrays
- No `useState`/`useEffect` in Server Components
- Stable unique keys in lists (not array index)
- Handle loading/error states for all data fetching
- No prop drilling past 3 levels - use context or composition

### Security (CRITICAL - checked before every commit)
- No hardcoded secrets (API keys, passwords, tokens)
- Parameterized queries (SQL injection prevention)
- Sanitized HTML output (XSS prevention)
- Rate limiting on public endpoints
- Error messages must not leak sensitive data
- Never commit .env files

### Testing
- 80% minimum coverage target
- Unit tests for all public functions
- Integration tests for API endpoints and database operations
- TDD workflow: write test first, verify failure, implement, verify pass

## Model Selection Strategy

- **Haiku**: Lightweight agents, simple code generation, worker tasks
- **Sonnet**: Main development work, code review, build fixes, TDD
- **Opus**: Complex architecture decisions, deep planning, research

## Context Window Management

- Avoid large-scale refactoring in the last 20% of context window
- Use Plan Mode for complex multi-file tasks
- Single-file edits are safe at any context level

## Git Conventions

- Commit format: `<type>: <description>` (feat, fix, refactor, docs, test, chore, perf, ci)
- PRs: analyze full commit history with `git diff [base-branch]...HEAD`
- Include test plan in PR descriptions
