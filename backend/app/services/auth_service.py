import os
import bcrypt
import jwt
import psycopg2
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify
from app.services.cache_service import get_db_conn

def register_user(email: str, password: str) -> dict:
    """Hash password and insert new user. Returns error if email taken."""
    pass_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn =  get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (email, pass_hash)
                VALUES (%s, %s)
                RETURNING id, email, role
            """, (email, pass_hash))
            row = cur.fetchone()
            conn.commit()
            return {"id": str(row[0]), "email": row[1], "role": row[2]}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"errors": "Email already registered"}
    finally:
        conn.close()

def login_user(email: str, password: str) -> dict:
    """Verify credentials and return a signed JWT token."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, pass_hash, role FROM users WHERE email = %s
            """, (email,))
            row = cur.fetchone()
    finally:
        conn.close()

    
    if not row:
        return {"error": "Invalid email or password"}
    
    user_id, pass_hash, role = row

    if not bcrypt.checkpw(password.encode(), pass_hash.encode()):
        return {"error": "Invalid email or password"}
    
    token = jwt.encode(
        {
            "user_id": str(user_id),
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        },
        os.environ["SECRET_KEY"],
        algorithm="HS256"
    )
    return {"token": token}

def decode_token(token: str) -> dict | None:
    """
    Decode and verify a JWT token.
    Returns the payload dict or None if invalid/expired.
    """
    try:
        return jwt.decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
    except jwt.PyJWKError:
        return None


def require_role(role: str):
    """Decorator: requires a valid JWT with the given role."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing token"}), 401
            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if payload is None:
                return jsonify({"error": "Invalid or expired token"}), 401
            if payload.get("role") != role:
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

