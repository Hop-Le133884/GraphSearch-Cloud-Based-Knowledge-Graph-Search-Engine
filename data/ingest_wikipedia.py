#!/usr/bin/env python3
"""
Wikipedia -> Neo4j enrichment script
Adds bio/Summary fields to existing Person ad Movie nodes.

Run with:
    docker compose exec backend python /data/ingest_wikipedia.py
"""

import os
import time
import requests
from neo4j import GraphDatabase

NEO4J_URI      = os.environ["NEO4J_URI"]
NEO4J_USER     = os.environ["NEO4J_USER"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

# Wikipedia REST API
WIKI_BASE    = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKI_HEADERS = {"User-Agent": "GraphSearch-Portfolio-Project/1.0"}

def fetch_wiki_summary(title):
    """
    Fetch the plain-text summary for a Wikipedia article by title.
    Returns the extract string, or None if not found.

    Wikipedia matches titles fuzzily — "Christopher Nolan" works,
    "Christopher_Nolan" also works (underscores auto-converted).
    """
    url = f"{WIKI_BASE}/{requests.utils.quote(title)}"