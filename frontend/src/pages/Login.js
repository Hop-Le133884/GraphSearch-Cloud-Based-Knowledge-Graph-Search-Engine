// Login page

import { userState, useState } from "react";
import {useNavigate, useLocation, Link } from "react-router-dom";
import { login } from "../api";

export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const naviage = useNavigate();
    const location = useLocation();
    const successMessage = location.state?.message;

    async function handleSubmit(e) {
        e.preventDefault();
        setError(null);
        const data = await login(email, password);

        if (data.error) {
            setError(data.error);
        } else {
            localStorage.setItem("token", data.token);
            naviage("/", { state: { message: `Welcome back, ${email}!` } });
        }
    }

    return (
        <div className="auth-page">
        <h2>Login</h2>
        {successMessage && <div style={{ color: "green", marginBottom: "12px" }}>{successMessage}</div>}
        <form onSubmit={handleSubmit}>
            <input
            type="email" placeholder="Email"
            value={email} onChange={e => setEmail(e.target.value)} required
            />
            <input
            type="password" placeholder="Password"
            value={password} onChange={e => setPassword(e.target.value)} required
            />
            <button type="submit">Login</button>
        </form>
        {error && <div className="error">{error}</div>}
        <p>No account? <Link to="/register">Register</Link></p>
        </div>
    );
}