import pytest
from app import create_app

@pytest.fixture
def client():
    """
    Flask test client.
    TESTING=True disables error propagation so we can assert on 4xx responses.
    """
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# Tests
def test_empty_query_returns_400(client):
    """
    No q param -> 400 Bad Request.
    """
    resp = client.get("/api/search")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_blank_query_returns_400(client):
    """q = (whitespace only) -> 400 Bad Request."""
    resp = client.get("/api/search?q=   ")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data

def test_valid_query_returns_results(client, monkeypatch):
    """
    Valid query → 200 with expected keys.
    monkeypatch replaces the real search() (OpenAI + Neo4j) with a fake.
    This keeps tests fast and free — no API calls made.
    """

    fake_result = {
        "query":   "Who directed Inception?",
        "cypher":  "MATCH (p:Person)-[:DIRECTED]->(m:Movie) RETURN p.name LIMIT 20",
        "results": [{"p.name": "Christopher Nolan", "p.pagerank_score": 0.001}],
        "count":   1,
    }

    monkeypatch.setattr("app.routes.search.search", lambda q: fake_result)

    resp = client.get("/api/search?q=Who+directed+Inception%3F")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 1
    assert "cypher" in data
    assert data["results"][0]["p.name"] == "Christopher Nolan"

def test_search_service_error_returns_500(client, monkeypatch):
    """
    If search() raises an exception → endpoint returns 500, not a crash.
    """
    def broken_search(q):
        raise RuntimeError("Neo4j connection failed")
    
    monkeypatch.setattr("app.routes.search.search", broken_search)

    resp = client.get("/api/search?q=Inception")
    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data