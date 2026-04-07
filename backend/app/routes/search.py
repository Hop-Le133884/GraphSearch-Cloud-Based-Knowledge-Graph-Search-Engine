from flask import Blueprint, request, jsonify
from app.services.graph_service import search

search_bp = Blueprint("search", __name__)

@search_bp.route("/api/search", methods=["GET"])
def search_endpoint():
    """
    GET /api/search?q=Who directed Inception?

    returns JSON:
    {
        "query": "Who directed Inception?",
        "cypher: "MATCH (p:Person)-[:DIRECTED]->Inception",
        "results": [...],
        "count": 1
    }
    """
    question = request.args.get("q", "").strip()

    if not question:
        return jsonify({"error": "Missing query parameter ?q="}), 400
    
    try:
        result = search(question)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500