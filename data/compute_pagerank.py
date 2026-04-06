#!/usr/bin/env python3
"""
Compute PageRank scores using Neo4j-side bipartite projection.

Strategy:
  - Let Cypher find co-star pairs and count shared movies (graph work stays in Neo4j)
  - NetworkX only runs the PageRank math on pre-weighted edges (more accurate)

Run with:
    docker compose exec backend python /data/compute_pagerank.py
"""

import os
import networkx as nx
from neo4j import GraphDatabase

NEO4J_URI      = os.environ["NEO4J_URI"]
NEO4J_USER     = os.environ["NEO4J_USER"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]


# -- Fetch weighted edges

def fetch_person_edges(session):
    """
    Find all Person pairs who share at least one movie (as actor or director).
    Returns weighted edges: more shared movies = stronger connection.

    WHERE elementId(p1) < elementId(p2) — prevents duplicate pairs.
    Without this, (DiCaprio, Pitt) and (Pitt, DiCaprio) would both appear,
    doubling every edge weight.

    count(m) — the number of shared movies becomes the edge weight.
    DiCaprio + Pitt sharing 3 movies is a stronger connection than sharing 1.
    """
    print("  Querying Person-Person weighted edges from Neo4j...")
    result = session.run("""
        MATCH (p1:Person)-[:ACTED_IN|DIRECTED]->(m:Movie)<-[:ACTED_IN|DIRECTED]-(p2:Person)
        WHERE elementId(p1) < elementId(p2)
        RETURN elementId(p1) AS source, elementId(p2) AS target, count(m) AS weight
    """)
    edges = [(r["source"], r["target"], {"weight": r["weight"]}) for r in result]
    print(f"  Person-Person edges: {len(edges)}")
    return edges


def fetch_movie_edges(session):
    """
    Find all Movie pairs that share at least one Person (actor or director).
    More shared persons = stronger connection.

    Inception and The Dark Knight both featuring Cillian Murphy
    → weight 1. Sharing 5 cast members → weight 5.
    """
    print("  Querying Movie-Movie weighted edges from Neo4j...")
    result = session.run("""
        MATCH (m1:Movie)<-[:ACTED_IN|DIRECTED]-(p:Person)-[:ACTED_IN|DIRECTED]->(m2:Movie)
        WHERE elementId(m1) < elementId(m2)
        RETURN elementId(m1) AS source, elementId(m2) AS target, count(p) AS weight
    """)
    edges = [(r["source"], r["target"], {"weight": r["weight"]}) for r in result]
    print(f"  Movie-Movie edges: {len(edges)}")
    return edges


# -- Run PageRank

def run_pagerank(edges, label):
    """
    Build undirected weighted graph and run PageRank.
    weight='weight' tells NetworkX to use our shared_count as edge strength.
    """
    print(f"  Building {label} graph...")
    G = nx.Graph()
    G.add_edges_from(edges)
    print(f"  {label} graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print(f"  Running weighted PageRank...")
    scores = nx.pagerank(G, alpha=0.85, weight="weight", max_iter=100, tol=1e-6)
    print(f"  Done. {len(scores)} nodes scored.")
    return scores


# -- Write scores to Neo4j 

def write_person_scores(session, scores):
    """
    Write pagerank_score to Person nodes using Neo4j internal elementId().
    The scores dict keys are Neo4j internal IDs — same ones Cypher used.
    """
    rows = [{"node_id": node_id, "score": score}
            for node_id, score in scores.items()]
    session.run("""
        UNWIND $rows AS row
        MATCH (p:Person) WHERE elementId(p) = row.node_id
        SET p.pagerank_score = row.score
    """, rows=rows)
    print(f"  Written pagerank_score to {len(rows)} Person nodes.")


def write_movie_scores(session, scores):
    rows = [{"node_id": node_id, "score": score}
            for node_id, score in scores.items()]
    session.run("""
        UNWIND $rows AS row
        MATCH (m:Movie) WHERE elementId(m) = row.node_id
        SET m.pagerank_score = row.score
    """, rows=rows)
    print(f"  Written pagerank_score to {len(rows)} Movie nodes.")


# -- Sanity check

def show_top_results(session):
    print("\n-- Top 10 Persons by PageRank")
    result = session.run("""
        MATCH (p:Person)
        WHERE p.pagerank_score IS NOT NULL
        RETURN p.name AS name, p.pagerank_score AS score
        ORDER BY score DESC LIMIT 10
    """)
    for i, row in enumerate(result, 1):
        print(f"  {i:2}. {row['name']:<30s}  {row['score']:.6f}")

    print("\n-- Top 10 Movies by PageRank")
    result = session.run("""
        MATCH (m:Movie)
        WHERE m.pagerank_score IS NOT NULL
        RETURN m.title AS title, m.pagerank_score AS score
        ORDER BY score DESC LIMIT 10
    """)
    for i, row in enumerate(result, 1):
        print(f"  {i:2}. {row['title']:<40s}  {row['score']:.6f}")


# -- Main

def main():
    print("=== Weighted PageRank (Neo4j projection + NetworkX) ===\n")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:

        print("Step 1: Fetching weighted edges from Neo4j...")
        person_edges = fetch_person_edges(session)
        movie_edges  = fetch_movie_edges(session)

        print("\nStep 2: Computing PageRank...")
        person_scores = run_pagerank(person_edges, "Person")
        movie_scores  = run_pagerank(movie_edges,  "Movie")

        print("\nStep 3: Writing scores to Neo4j...")
        write_person_scores(session, person_scores)
        write_movie_scores(session, movie_scores)

        print("\nStep 4: Sanity check...")
        show_top_results(session)

    driver.close()
    print("\nDone!")


if __name__ == "__main__":
    main()