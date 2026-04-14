import { useState } from "react";
import "./App.css";

const API = "http://localhost:5000";

function ResultCard({ result }) {
  // result keys vary by query — render whatever keys come back
  const entries = Object.entries(result);
  const nameEntry = entries.find(([k]) => k.includes("name") || k.includes("title"));
  const scoreEntry = entries.find(([k]) => k.includes("pagerank"));
  const bioEntry = entries.find(([k]) => k.includes("bio") || k.includes("overview"));

  return (
    <div className="card">
      {nameEntry && <h3>{nameEntry[1]}</h3>}
      {scoreEntry && (
        <div className="score">
          PageRank: {scoreEntry[1] ? scoreEntry[1].toFixed(6) : "n/a"}
        </div>
      )}
      {bioEntry && bioEntry[1] && <p>{bioEntry[1]}</p>}
    </div>
  );
}

export default function App() {
  const [query, setQuery]     = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const resp = await fetch(
        `${API}/api/search?q=${encodeURIComponent(query)}`
      );
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Search failed");
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <h1>GraphSearch</h1>
      <p className="subtitle">Natural language search over a movie knowledge graph</p>

      <form className="search-box" onSubmit={handleSearch}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Who directed Inception?"
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {results && (
        <>
          <div className="meta">
            {results.count} result{results.count !== 1 ? "s" : ""}
            <span className={`cache-badge ${results.cache_hit ? "hit" : "miss"}`}>
              {results.cache_hit ? "cached" : "live"}
            </span>
          </div>

          {results.results.map((r, i) => (
            <ResultCard key={i} result={r} />
          ))}

          <div className="cypher-label">Generated Cypher</div>
          <div className="cypher">{results.cypher}</div>
        </>
      )}
    </div>
  );
}
