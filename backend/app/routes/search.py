from flask import Blueprint, request, jsonify
from app.services.graph_service import search
import time
from app.services.cache_service import hash_query, get_cached_result, save_to_cache, log_query

search_bp = Blueprint("search", __name__)



@search_bp.route("/api/search", methods=["GET"])
def search_endpoint():
    question = request.args.get("q", "").strip()

    if not question:
        return jsonify({"error": "Missing query parameter ?q="}), 400
    
    query_hash = hash_query(question)
    start = time.time()

    try:
        cached = get_cached_result(query_hash)
        if cached:
            latency_ms = int((time.time() - start) * 1000)
            log_query(question, query_hash, cypher=None,
                      latency_ms=latency_ms, result_count=cached.get("count", 0),
                      cache_hit=True)
            cached["cache_hit"] = True
            return jsonify(cached), 200
        
        # Cache miss - run the full pipeline
        result = search(question)
        latency_ms = int((time.time() - start) * 1000)

        save_to_cache(query_hash, question, result)
        log_query(question, query_hash, cypher=result.get("cypher"),
                  latency_ms=latency_ms, result_count=result.get("count", 0),
                  cache_hit=False)
        
        result["cache_hit"] = False
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500