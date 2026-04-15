const API = process.env.REACT_APP_API_URL || "http://localhost:5000";

export async function searchQuery(q) {
    const resp = await fetch(`${API}/api/search?q=${encodeURIComponent(q)}`);
    return resp.json();
}

export async function register(email, password) {
    const resp = await fetch(`${API}/api/auth/register`, { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password}),
    });
    return resp.json();
}

export async function login(email, password) {
    const resp = await fetch(`${API}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password}),
    });
    return resp.json();
}

export async function getAnalytics() {
    const token = localStorage.getItem("token");
    const resp = await fetch(`${API}/api/analytics`, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
    });
    return resp.json();
}