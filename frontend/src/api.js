const API = "http://localhost:5000";

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
    const resp = await fetch(`${API}/api/analytics`);
    return resp.json();
}