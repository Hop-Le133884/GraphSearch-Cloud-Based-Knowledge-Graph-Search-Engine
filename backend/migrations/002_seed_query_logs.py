import psycopg2
import hashlib
import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Realistic query distribution — some queries are much more common
QUERIES = [
    ("Who directed Inception?", 0.12),
    ("Movies starring Leonardo DiCaprio", 0.10),
    ("Top action movies", 0.08),
    ("Who produced Interstellar?", 0.06),
    ("Movies directed by Christopher Nolan", 0.06),
    ("Who acted in The Dark Knight?", 0.05),
    ("Top 10 actors by pagerank", 0.05),
    ("Movies starring Tom Hanks", 0.04),
    ("Who directed Avengers Endgame?", 0.04),
    ("Best sci-fi movies", 0.03),
    ("Movies from 2019", 0.03),
    ("Who is Leonardo DiCaprio?", 0.03),
    ("Action movies with high revenue", 0.02),
    ("Movies produced by Marvel", 0.02),
    ("Who directed The Departed?", 0.02),
    ("Movies starring Scarlett Johansson", 0.02),
    ("Top horror movies", 0.02),
    ("Who directed Oppenheimer?", 0.02),
    ("Movies starring Brad Pitt", 0.02),
    ("Directors with most movies", 0.02),
]

# Normalize weights to sum to 1
total = sum(w for _, w in QUERIES)
QUERIES = [(q, w / total) for q, w in QUERIES]

def hash_query(text):
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()

def seed(n=50000):
    conn = psycopg2.connect(
        host="pgbouncer", port=5432,
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )

    query_texts = [q for q, _ in QUERIES]
    weights     = [w for _, w in QUERIES]

    # Spread rows over the last 30 days
    now = datetime.utcnow()

    batch = []
    for i in range(n):
        query_text = random.choices(query_texts, weights=weights)[0]
        query_hash = hash_query(query_text)
        cache_hit  = random.random() < 0.65        # 65% cache hit rate
        latency_ms = random.randint(30, 80) if cache_hit else random.randint(800, 2500)
        created_at = now - timedelta(
            seconds=random.randint(0, 30 * 24 * 3600)
        )
        batch.append((query_text, query_hash, latency_ms, cache_hit, created_at))

        if len(batch) == 1000:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO query_logs
                        (query_text, query_hash, latency_ms, cache_hit, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, batch)
            conn.commit()
            print(f"  Inserted {i+1} rows...")
            batch = []

    if batch:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO query_logs
                    (query_text, query_hash, latency_ms, cache_hit, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, batch)
        conn.commit()

    conn.close()
    print(f"Done. {n} rows inserted into query_logs.")

if __name__ == "__main__":
    seed(50000)
