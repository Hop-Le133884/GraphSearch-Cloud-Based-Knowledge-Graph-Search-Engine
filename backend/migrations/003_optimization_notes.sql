-- =============================================
-- BASELINE (no indexes)
-- =============================================
-- Query: top queries in last 7 days
-- "QUERY PLAN"
-- Query: top queries in last 7 days
-- Plan:  Seq Scan on query_logs
--        Rows scanned: 50,076
--        Rows removed by filter: 38,509
-- "  Buffers: shared hit=91"
-- "Planning Time: 1.032 ms"
-- "Execution Time: 20.146 ms"

-- Problem: full table scan on every analytics request.
-- Fix: index on created_at so PostgreSQL can skip old rows.
-- =============================================
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT query_text, COUNT(*) AS freq
FROM query_logs
WHERE created_at > now() - INTERVAL '7 days'
GROUP BY query_text
ORDER BY freq DESC
LIMIT 10;

-- =============================================
-- AFTER: idx_logs_created added
-- =============================================
-- Plan:  Bitmap Index Scan on idx_logs_created
--        Rows scanned: 11,244 (skipped 38,832 old rows)
--        Execution Time: 7.584 ms
--
-- Improvement: 10.993ms → 7.584ms (~31% faster)
-- Scan changed from Seq Scan to Bitmap Index Scan
-- =============================================


-- =============================================
-- LOAD TEST RESULTS (locust, 50 concurrent users, 60s)
-- =============================================
-- /api/search [cached]: avg 28ms, median 23ms, 19 req/s, 0 failures
-- /api/analytics:       avg 48ms, median 45ms,  5 req/s, 0 failures
-- Aggregated:           avg 33ms, median 27ms, 25 req/s, 0 failures
--
-- PgBouncer pool_size=10 served 50 concurrent users with 0 failures.
-- PostgreSQL connections held: 10 (not 50).
-- =============================================
