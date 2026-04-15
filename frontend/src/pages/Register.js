// Register page

import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "../api";

export default function Register() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    async function handleSubmit(e) {
        e.preventDefault();
        setError(null);
        const data = await register(email, password);
        if (data.error) {
            setError(data.error);
        } else {
            navigate("/login", { state: { message: "Account created! Please log in." } });
        }
    }

    return (
        <div className="auth-page">
        <h2>Register</h2>
        <form onSubmit={handleSubmit}>
            <input
            type="email" placeholder="Email"
            value={email} onChange={e => setEmail(e.target.value)} required
            />
            <input
            type="password" placeholder="Password"
            value={password} onChange={e => setPassword(e.target.value)} required
            />
            <button type="submit">Register</button>
        </form>
        {error && <div className="error">{error}</div>}
        <p>Have an account? <Link to="/login">Login</Link></p>
        </div>
    );
}