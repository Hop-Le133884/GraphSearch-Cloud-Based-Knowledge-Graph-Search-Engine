# GraphSearch — Cloud-Based Knowledge Graph Search Engine

A semantic search engine that converts natural language queries into Neo4j graph traversals, backed by PostgreSQL for caching, auth, and analytics — with a React frontend and Grafana monitoring.

**Example:** Ask `"Who directed Inception?"` → LangChain converts it to Cypher → runs against Neo4j → returns Christopher Nolan with bio and PageRank score. Repeated queries are served from PostgreSQL cache (~28x faster).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                           │
│         Search bar → Result cards → Analytics dashboard             │
│         Login / Register pages → JWT stored in localStorage         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────────────┐
│                      BACKEND (Python + Flask)                       │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐      │
│  │ /api/search  │  │  /api/auth   │  │  /api/analytics       │      │
│  │  LangChain   │  │  register    │  │  top queries          │      │
│  │  → Cypher    │  │  login (JWT) │  │  avg latency          │      │
│  │  → Neo4j     │  │              │  │  cache hit rate       │      │
│  │  → PG cache  │  │              │  │                       │      │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘      │
└─────────┼─────────────────┼──────────────────────┼──────────────────┘
          │                 │                      │
    ┌─────▼─────┐     ┌─────▼──────────────────────▼───────┐
    │   Neo4j   │     │          PostgreSQL                 │
    │  AuraDB   │     │  users, query_logs, result_cache    │
    └───────────┘     │  PgBouncer (connection pooling)     │
                      └────────────────────────────────────┘
                                     │
                      ┌──────────────▼──────────────┐
                      │     Grafana (port 3001)      │
                      │  latency · cache · queries   │
                      └─────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Graph database | Neo4j AuraDB Free |
| NL → Cypher | LangChain + GPT-4o-mini |
| Graph ranking | NetworkX (weighted PageRank) |
| Backend | Python, Flask, psycopg2 |
| Cache + auth DB | PostgreSQL 16 + PgBouncer |
| Auth | bcrypt + JWT (PyJWT) |
| Frontend | React, React Router, Recharts |
| Monitoring | Grafana |
| Containerization | Docker Compose |
| Data source | TMDB API (536 movies, 4276 persons) |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Neo4j AuraDB Free](https://neo4j.com/cloud/aura/) account — free cloud-hosted graph database
- [TMDB API](https://www.themoviedb.org/settings/api) account — free movie database API
- [OpenAI API](https://platform.openai.com/) key — used for NL → Cypher translation (gpt-4o-mini)

---

## Project Structure

```
GraphSearch/
├── docker-compose.yml          # PostgreSQL + PgBouncer + Flask + React + Grafana
├── .env                        # your secrets (not committed)
├── .env.example                # template for .env
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py                  # Flask entry point
│   ├── migrations/
│   │   ├── 001_schema.sql           # users, query_logs, result_cache tables
│   │   ├── 002_seed_query_logs.py   # seeds 50K rows for benchmarking
│   │   └── 003_optimization_notes.sql  # EXPLAIN ANALYZE before/after results
│   ├── app/
│   │   ├── __init__.py         # app factory, registers blueprints
│   │   ├── config.py           # reads env vars
│   │   ├── routes/
│   │   │   ├── search.py       # GET /api/search
│   │   │   ├── auth.py         # POST /api/auth/register, /api/auth/login
│   │   │   └── analytics.py    # GET /api/analytics
│   │   └── services/
│   │       ├── graph_service.py   # NL → Cypher → Neo4j pipeline
│   │       ├── cache_service.py   # PostgreSQL cache + query logging
│   │       └── auth_service.py    # bcrypt + JWT
│   └── tests/
│       ├── test_search.py      # pytest suite
│       └── locustfile.py       # load test (50 concurrent users)
│
├── frontend/
│   └── src/
│       ├── App.js              # router, nav, search page
│       ├── api.js              # all fetch calls to backend
│       └── pages/
│           ├── Login.js
│           ├── Register.js
│           └── Analytics.js    # stats cards + bar chart
│
└── data/
    ├── ingest_tmdb.py          # pulls TMDB data into Neo4j
    └── compute_pagerank.py     # computes PageRank scores via NetworkX
```

---

## Setup

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd GraphSearch-Cloud-Based-Knowledge-Graph-Search-Engine

cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
SECRET_KEY=any-random-string

POSTGRES_DB=graphsearch
POSTGRES_USER=graphsearch
POSTGRES_PASSWORD=choose-a-password

# From Neo4j AuraDB console after creating a free instance
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password

# From TMDB → Settings → API → API Read Access Token (Bearer token, starts with ey...)
TMDB_API_TOKEN=your-tmdb-token

# From OpenAI platform
OPENAI_API_KEY=sk-...
```

---

### 2. Start the containers

```bash
docker compose up --build -d
```

This starts five services:

| Service | Port | Purpose |
|---------|------|---------|
| `db` | 5433 | PostgreSQL |
| `pgbouncer` | 6432 | Connection pooler |
| `backend` | 5000 | Flask API |
| `frontend` | 3000 | React dev server |
| `grafana` | 3001 | Monitoring dashboard |

Verify:
```bash
docker compose ps
curl http://localhost:5000/health   # → {"status": "ok"}
```

---

### 3. Apply the database schema

```bash
docker compose exec -T db bash -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB' < backend/migrations/001_schema.sql
```

Verify:
```bash
docker compose exec db bash -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"'
# → users, query_logs, result_cache
```

---

### 4. Ingest movie data into Neo4j

Pulls 500 popular movies + cast + directors from TMDB into Neo4j AuraDB. Takes ~5-10 minutes.

> **Note:** Neo4j AuraDB Free pauses after 3 days of inactivity. Resume it from the AuraDB console before running this.

```bash
docker compose exec backend python /data/ingest_tmdb.py
```

Expected output:
```
Node counts:
  Person: 4276  |  Movie: 536  |  Genre: 19  |  Company: 690
```

---

### 5. Compute PageRank scores

```bash
docker compose exec backend python /data/compute_pagerank.py
```

Expected output:
```
Top 5 persons by PageRank:
  Leonardo DiCaprio: 0.00312
  Ralph Fiennes: 0.00298
  ...
```

---

## Using the App

Open `http://localhost:3000` in your browser.

- **Search** — type any natural language question about movies
- **Register / Login** — create an account, JWT token stored in localStorage
- **Analytics** — see top queries, cache hit rate, average latency
- **Grafana** — open `http://localhost:3001` (admin / admin) for live metrics

---

## API Endpoints

### Search
```bash
GET /api/search?q=Who directed Inception?
```
Response includes `cache_hit: true/false` — repeated queries skip Neo4j entirely.

### Auth
```bash
POST /api/auth/register   { "email": "...", "password": "..." }
POST /api/auth/login      { "email": "...", "password": "..." }
# login returns { "token": "eyJ..." }
```

### Analytics
```bash
GET /api/analytics
# → { total_queries, cache_hit_rate, avg_latency_ms, top_queries }
```

---

## Running Tests

```bash
docker compose exec backend pytest tests/ -v
```

```
tests/test_search.py::test_empty_query_returns_400          PASSED
tests/test_search.py::test_blank_query_returns_400          PASSED
tests/test_search.py::test_valid_query_returns_results      PASSED
tests/test_search.py::test_search_service_error_returns_500 PASSED

4 passed in 0.54s
```

---

## Stopping the project

```bash
# Stop containers (data preserved)
docker compose down

# Stop and delete all local data (PostgreSQL + Grafana volumes)
docker compose down -v
```

If you wipe with `-v`, re-run steps 3 and 5 (schema migration + PageRank).
Neo4j AuraDB is a cloud service and is unaffected by `down -v`.

---

## Performance Optimizations

All benchmarks on a 50K+ row `query_logs` table.

---

### 1. Query Result Cache (~28x faster for repeated queries)

Repeated identical queries are served from PostgreSQL `result_cache` instead of calling OpenAI + Neo4j.

| Path | Avg latency |
|------|------------|
| Cache miss (OpenAI + Neo4j) | ~1,100ms |
| Cache hit (PostgreSQL) | ~38ms |

---

### 2. PostgreSQL Index on `created_at` (~70% faster analytics)

The analytics query filters `query_logs` by time range. Without an index, PostgreSQL reads every row.

**Before:**
```
Seq Scan on query_logs
Rows scanned:  51,146  |  Rows removed by filter: 39,143
Execution time: 18.654ms
```

**After (`CREATE INDEX idx_logs_created ON query_logs (created_at DESC)`):**
```
Bitmap Index Scan on idx_logs_created
Rows scanned:  12,002 (skipped 39,143 old rows)
Execution time: 5.674ms
```

---

### 3. Materialized View for Analytics (~22x faster aggregation)

`GET /api/analytics` previously ran a full aggregation over 50K+ rows on every request.

**Before:**
```
Seq Scan on query_logs  —  51,146 rows  —  15.355ms
```

**After (materialized view `search_stats` with hourly pre-aggregation):**
```
Seq Scan on search_stats  —  724 rows  —  0.693ms
```

Refresh after new data:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY search_stats;
```

---

### 4. PgBouncer Connection Pooling (0 failures at 50 concurrent users)

PgBouncer in transaction pool mode (`pool_size=10`) serves 50 concurrent users through 10 reused PostgreSQL connections.

**Load test (locust, 50 users, 60 seconds):**

| Endpoint | Avg | Median | Max | Req/s | Failures |
|----------|-----|--------|-----|-------|----------|
| `/api/search` (cached) | 28ms | 23ms | 291ms | 19/s | 0 |
| `/api/analytics` | 48ms | 45ms | 106ms | 5/s | 0 |
| Aggregated | 33ms | 27ms | 291ms | 25/s | 0 |
