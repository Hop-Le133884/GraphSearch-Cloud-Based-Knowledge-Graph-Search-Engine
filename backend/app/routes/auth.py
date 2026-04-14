from flask import Blueprint, request, jsonify
from app.services.auth_service import register_user, login_user


auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/auth/register", methods=["POST"])

def register():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "email and password required"}), 400
    
    result = register_user(data["email"], data["password"])

    if "error" in result:
        return jsonify(result), 409 # 409 Conflict - email already taken
    
    return jsonify(result), 201

@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "email and password required"}), 400
    
    result = login_user(data["email"], data["password"])

    if "error" in result:
        return jsonify(result), 401
    
    return jsonify(result), 200

