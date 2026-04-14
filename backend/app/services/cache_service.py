import hashlib
import json
import time
import psycopg2
import os


def get_db_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )

def hash_query(query_text: str) -> str:
    """SHA-256 hash of lowercased query - cache key."""
    normalized = query_text.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()

def get_cached_result(query_hash: str) -> dict | None:
    """
    Returns cached results if found and not expired, else None.
    Also increments hit_count on cache hit.
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT result_json FROM result_cache
                WHERE query_hash = %s AND expires_at > now()
            """, (query_hash,))
            row = cur.fetchone()
            
            if row:
                # Increment hit counter
                cur.execute("""
                    UPDATE result_cache SET hit_count = hit_count + 1
                    WHERE query_hash = %s
                """, (query_hash,))
                conn.commit()
                return row[0]   # psycopg2 returns JSONB as a Python dict already
            return None
    finally:
        conn.close()

def save_to_cache(query_hash: str, query_text: str, results: dict):
    """Insert results into cache. If same hash exists, do nothing (ON CONFLICT)."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO result_cache (query_hash, query_text, result_json)
                VALUES (%s, %s, %s)
                ON CONFLICT (query_hash) DO NOTHING
            """, (query_hash, query_text, json.dumps(results)))
            conn.commit()
    finally:
        conn.close()

def log_query(query_text: str, query_hash: str, cypher: str,
              latency_ms: int, result_count: int, cache_hit: bool,
              user_id=None):
    """Write one row to query_logs."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO query_logs
                    (user_id, query_text, query_hash, cypher_query,
                     latency_ms, result_count, cache_hit)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, query_text, query_hash, cypher,
                  latency_ms, result_count, cache_hit))
            conn.commit()
    finally:
        conn.close()