# GraphSearch — Architecture & Build Plan

**GraphSearch: Cloud-Based Knowledge Graph Search Engine**
A semantic search engine that converts natural language queries into Neo4j graph traversals, backed by PostgreSQL for query caching, user management, and search analytics — deployed on AWS with full CI/CD.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                          │
│              Search bar → Results display → Analytics page         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────────────┐
│                      BACKEND (Python + Flask)                      │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │  /api/search  │  │  /api/auth   │  │  /api/analytics       │    │
│  │              │  │              │  │                       │    │
│  │  1. Check PG │  │  JWT auth    │  │  Top queries, avg     │    │
│  │     cache    │  │  User CRUD   │  │  latency, graph stats │    │
│  │  2. If miss: │  │              │  │                       │    │
│  │     LangChain│  │              │  │                       │    │
│  │     → Cypher │  │              │  │                       │    │
│  │     → Neo4j  │  │              │  │                       │    │
│  │  3. Cache hit│  │              │  │                       │    │
│  │     in PG    │  │              │  │                       │    │
│  │  4. Log query│  │              │  │                       │    │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘    │
│         │                 │                      │                 │
└─────────┼─────────────────┼──────────────────────┼─────────────────┘
          │                 │                      │
    ┌─────▼─────┐    ┌─────▼──────────────────────▼──────┐
    │   Neo4j   │    │          PostgreSQL (RDS)          │
    │  AuraDB   │    │                                    │
    │           │    │  users          – auth, roles      │
    │  Nodes:   │    │  query_logs     – every search     │
    │  Person   │    │  result_cache   – cached responses │
    │  Movie    │    │  search_stats   – materialized     │
    │  Genre    │    │                   analytics view   │
    │  Company  │    │                                    │
    │           │    │  PgBouncer (connection pooling)     │
    │  Edges:   │    │  Indexes on (query_hash, user_id,  │
    │  DIRECTED │    │            created_at)             │
    │  ACTED_IN │    │                                    │
    │  GENRE_OF │    └────────────────────────────────────┘
    │  WORKS_AT │
    └───────────┘
```

---

## Data Flow — Search Request Lifecycle

```
User types: "Who directed movies starring Tom Hanks?"
        │
        ▼
   [1] Flask receives query string
        │
        ▼
   [2] Hash the query → check PostgreSQL result_cache
        │
        ├── CACHE HIT → return cached results (fast path)
        │                log query with cache_hit=true
        │
        └── CACHE MISS ↓
        │
        ▼
   [3] LangChain parses natural language → Cypher query
       "MATCH (p:Person {name:'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person)
        RETURN d.name, m.title"
        │
        ▼
   [4] Execute Cypher against Neo4j AuraDB
        │
        ▼
   [5] Apply ranking (PageRank scores pre-computed in Neo4j GDS)
        │
        ▼
   [6] Write results to PostgreSQL result_cache
       Log query to query_logs (query text, latency_ms, result_count,
       cache_hit=false, timestamp)
        │
        ▼
   [7] Return JSON response to frontend
```

## Project Structure

