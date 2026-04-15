from flask import Flask
from flask_cors import CORS
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    # Health check - verifies Flask is up and Neo4j is reachable
    @app.route("/health")
    def health():
        import os
        from neo4j import GraphDatabase
        try:
            driver = GraphDatabase.driver(
                os.environ["NEO4J_URI"],
                auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
            )
            driver.verify_connectivity()
            driver.close()
            neo4j_status = "ok"
        except Exception:
            neo4j_status = "down"
        return {"status": "ok", "neo4j": neo4j_status}, 200
    
    # blueprints
    from app.routes.search import search_bp
    app.register_blueprint(search_bp)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp)
    return app