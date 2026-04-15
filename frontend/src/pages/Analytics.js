// Analytics page

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getAnalytics } from "../api";

export default function Analytics() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        getAnalytics()
            .then(setData)
            .catch(err => setError(err.message));
    }, []);

    if (error) return <div className="error">{error}</div>;
    if (!data)  return <div className="app"><p>Loading...</p></div>;

    return (
        <div className="app">
        <h1>Analytics</h1>

        <div className="stats-grid">
            <div className="stat-card">
            <div className="stat-value">{data.total_queries}</div>
            <div className="stat-label">Total Queries</div>
            </div>
            <div className="stat-card">
            <div className="stat-value">{data.cache_hit_rate}%</div>
            <div className="stat-label">Cache Hit Rate</div>
            </div>
            <div className="stat-card">
            <div className="stat-value">{data.avg_latency_cached_ms}ms</div>
            <div className="stat-label">Avg Latency (Cached)</div>
            </div>
            <div className="stat-card">
            <div className="stat-value">{data.avg_latency_live_ms}ms</div>
            <div className="stat-label">Avg Latency (Live)</div>
            </div>
        </div>

        <h2 style={{ margin: "32px 0 16px" }}>Top Queries</h2>
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.top_queries} layout="vertical"
            margin={{ left: 180, right: 20 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="query" width={180} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="count" fill="#4a90e2" />
            </BarChart>
        </ResponsiveContainer>
        </div>
    );
}