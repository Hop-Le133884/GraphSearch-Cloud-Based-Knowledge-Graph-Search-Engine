#!/usr/bin/env python3

"""
TMDB -> Neo4j ingestion script
Pulls top 500 popular movies with cast, directors, genres, and production companies.

Run with:
    docker compose exec backend python /data/ingest_tmdb.py
"""

import os
import time
import requests
from neo4j import GraphDatabase

# Inside the container, Docker Compose already injects env vars.
# These will ratese keyError immediately if a variable is missing ---> fast feedback.
TMDB_TOKEN = os.environ["TMDB_API_TOKEN"]
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USER = os.environ["NEO4J_USER"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

TMDB_BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {TMDB_TOKEN}"}

# -- TMDB fetching
def tmdb_get(path, params=None):
    """GET a TMDB endpoint, return parsed JSON"""
    resp = requests.get(f"{TMDB_BASE}{path}", headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_popular_movie_ids(pages=25):
    """Fetch IDs of the top ~500 popular movies (20 results per page)."""
    ids = []
    for page in range(1, pages + 1):
        data = tmdb_get("/movie/popular", params={"page": page})
        ids.extend(m["id"] for m in data["results"])
        print(f" Page {page}/{pages} - {len(ids)} movie IDs collected")
        time.sleep(0.1) # TMDB rate limit: ~40 req/s, stay well under
    return ids

def fetch_movie_data(movie_id):
    """Fetch full details + credits for one movie. Returns structred dict"""
    details = tmdb_get(f"/movie/{movie_id}")
    credits = tmdb_get(f"/movie/{movie_id}/credits")
    time.sleep(0.05)

    directors = [p for p in credits.get("crew", []) if p.get("job") == "Director"]
    cast = credits.get("cast", [])[:10] # top 10 billed actors only

    return {
        "movie": {
            "tmdb_id": details["id"],
            "title": details["title"],
            "released": (details.get("release_date") or "")[:4] or None,
            "tagline": details.get("tagline", ""),
            "revenue": details.get("revenue", 0),
        },
        "genres": [
            {"name": g["name"]}
            for g in details.get("genres", [])
        ],
        "companies": [
            {"name": c["name"], "country": c.get("origin_country", "")}
            for c in details.get("production_companies", [])[:3] # top 3
        ],
        "directors": [
            {"tmdb_id": p["id"], "name": p["name"]}
            for p in directors
        ],
        "cast": [
            {"tmdb_id": p["id"], "name": p["name"], "role": p.get("character", "")}
            for p in cast
        ],
    }

# Neo4j writing
def create_constraints(session):
    """
    Uniqueness constraints prevent duplicates nodes and auto-create indexes.
    MERGE relies on these - without them, MERGE does a full scan every time.
    """
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Movie) REQUIRE m.tmdb_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.tmdb_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
    ]
    for stmt in constraints:
        session.run(stmt)
    print(" Constraints ready.")

def ingest_batch(session, batch):
    """
    Write a list of movie records to Neo4j using UNWIND for batch efficiency.
    
    MERGE = "Create if not exists, match if exists" - safe to re-run.
    UNWIND = send a list to Cypher and process each item in one query,
    """
    # Movies
    session.run("""
        UNWIND $movies AS m
        MERGE (movie:Movie {tmdb_id: m.tmdb_id})
        SET movie.title = m.title,
            movie.released = m.released,
            movie.tagline = m.tagline,
            movie.revenue = m.revenue
    """, movies=[r["movie"] for r in batch])

    # Genres and GENRE_OF relationships
    session.run("""
        UNWIND $rows AS row
        MERGE (movie:Movie {tmdb_id: row.tmdb_id})
        WITH movie, row
        UNWIND row.genres AS g
        MERGE (genre:Genre {name: g.name})
        MERGE (movie)-[:GENRE_OF]->(genre)
    """, rows=[{"tmdb_id": r["movie"]["tmdb_id"], "genres": r["genres"]} for r in batch])

    # Directors + DIRECTED relationships
    session.run("""
        UNWIND $rows AS row
        MERGE (movie:Movie {tmdb_id: row.tmdb_id})
        WITH movie, row
        UNWIND row.directors AS d
        MERGE (person:Person {tmdb_id: d.tmdb_id})
        SET person.name = d.name
        MERGE (person)-[:DIRECTED]->(movie)
    """, rows=[{"tmdb_id": r["movie"]["tmdb_id"], "directors": r["directors"]} for r in batch])

    # Cast + ACTED_IN relationships
    session.run("""
        UNWIND $rows AS row
        MERGE (movie:Movie {tmdb_id: row.tmdb_id})
        WITH movie, row
        UNWIND row.cast AS c
        MERGE (person:Person {tmdb_id: c.tmdb_id})
        SET person.name = c.name
        MERGE (person)-[:ACTED_IN {role:c.role}]->(movie)
        """, rows=[{"tmdb_id": r["movie"]["tmdb_id"], "cast": r["cast"]} for r in batch])
    
    # Production companies + PRODUCED_BY
    session.run("""
        UNWIND $rows AS row
        MERGE (movie:Movie {tmdb_id: row.tmdb_id})
        WITH movie, row
        UNWIND row.companies AS c
        MERGE (company:Company {name: c.name})
        SET company.country = c.country
        MERGE (movie)-[:PRODUCED_BY]->(company)
    """, rows=[{"tmdb_id": r["movie"]["tmdb_id"], "companies": r["companies"]} for r in batch])


# -- Main
def main():
    print(" === TMDB -> Neo4j Ingestion ===\n")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        print("Step 1: Creating constraints...")
        create_constraints(session)

        print("\nStep 2: Fetching movie IDs from TMDB...")
        movie_ids = fetch_popular_movie_ids(pages=25)
        print(f" Total: {len(movie_ids)} movies to process\n")

        print("Step 3: Fetching details + ingesting to Neo4j...")
        batch = []
        skipped = 0

        for i, movie_id in enumerate(movie_ids, 1):
            try:
                data = fetch_movie_data(movie_id)
                batch.append(data)

                if len(batch) >= 20: # flush every 20 movie_ids
                    ingest_batch(session, batch)
                    batch = []
                    print(f" {i}/{len(movie_ids)} ingested...")

            except Exception as e:
                skipped += 1
                print(f" Skipped movie {movie_id}: {e}")

        if batch:
            ingest_batch(session, batch)

        # Summary
        print("\n=== Node Counts in Neo4j ===")
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            ORDER BY count DESC
        """)
        for row in result:
            print(f"  {row['label']}: {row['count']}")

        if skipped:
            print(f"\n  ({skipped} movies skipped due to errors)")

    driver.close()
    print("\nDone!")


if __name__ == "__main__":
    main()