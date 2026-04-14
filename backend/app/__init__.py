from flask import Flask
from flask_cors import CORS
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    # Health check - lets Docker/load balancer verify the app is alive
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200
    
    # blueprints
    from app.routes.search import search_bp
    app.register_blueprint(search_bp)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    
    return app