import { useState } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Analytics from "./pages/Analytics";
import { searchQuery } from "./api";
import "./App.css";

function ResultCard({ result }) {
  const entries = Object.entries(result);
  const nameEntry  = entries.find(([k]) => k.includes("name") || k.includes("title"));
  const scoreEntry = entries.find(([k]) => k.includes("pagerank"));
  const bioEntry   = entries.find(([k]) => k.includes("bio") || k.includes("overview"));

  return (
    <div className="card">
      {nameEntry  && <h3>{nameEntry[1]}</h3>}
      {scoreEntry && (
        <div className="score">
          PageRank: {scoreEntry[1] ? scoreEntry[1].toFixed(6) : "n/a"}
        </div>
      )}
      {bioEntry && bioEntry[1] && <p>{bioEntry[1]}</p>}
    </div>
  );
}

function SearchPage() {
  const [query, setQuery]     = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const location = useLocation();
  const welcomeMessage = location.stage?.message;

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await searchQuery(query);
      if (data.error) throw new Error(data.error);
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
    
      {welcomeMessage && <div style={{ color: "green", marginBottom: "12px" }}>{welcomeMessage}</div>}
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
          {results.results.map((r, i) => <ResultCard key={i} result={r} />)}
          <div className="cypher-label">Generated Cypher</div>
          <div className="cypher">{results.cypher}</div>
        </>
      )}
    </div>
  );
}

function Nav() {
  const token = localStorage.getItem("token");
  return (
    <nav style={{ background: "white", borderBottom: "1px solid #e0e0e0",
                  padding: "12px 24px", display: "flex", gap: "20px" }}>
      <Link to="/">Search</Link>
      <Link to="/analytics">Analytics</Link>
      {token
        ? <span style={{ marginLeft: "auto", cursor: "pointer", color: "#888" }}
            onClick={() => { localStorage.removeItem("token"); window.location.reload(); }}>
            Logout
          </span>
        : <>
            <Link to="/login" style={{ marginLeft: "auto" }}>Login</Link>
            <Link to="/register">Register</Link>
          </>
      }
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/"          element={<SearchPage />} />
        <Route path="/login"     element={<Login />} />
        <Route path="/register"  element={<Register />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </BrowserRouter>
  );
}
