from flask import Blueprint, jsonify
from app.services.cache_service import get_db_conn


analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/api/analytics", methods=["GET"])
def analytics():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:

            # Total queries
            cur.execute("SELECT COUNT(*) FROM query_logs")
            total_queries = cur.fetchone()[0]

            # Cache hit rate
            cur.execute("""
                SELECT
                    ROUND(
                        100.0 * SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS hit_rate
                FROM query_logs                        
            """)
            cache_hit_rate = cur.fetchone()[0]

            # Average latency
            cur.execute("SELECT ROUND(AVG(latency_ms)) FROM query_logs")
            avg_latency_ms = cur.fetchone()[0]

            # Top 10 most searched queries
            cur.execute("""
                SELECT query_text, COUNT(*) AS freq
                FROM query_logs
                GROUP BY query_text
                ORDER BY freq DESC
                LIMIT 10
            """)
            top_queries = [
                {"query": row[0], "count": row[1]}
                for row in cur.fetchall()
            ]

        return jsonify({
            "total_queries":   total_queries,
            "cache_hit_rate":  float(cache_hit_rate or 0),
            "avg_latency_ms":  float(avg_latency_ms or 0),
            "top_queries":     top_queries,
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
