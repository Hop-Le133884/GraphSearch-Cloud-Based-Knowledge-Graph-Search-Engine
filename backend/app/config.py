import os

class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # PostgreSQL
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "db")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "graphsearch")
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "graphsearch")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")


    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Neo4j
    NEO4J_URI = os.environ.get("NEO4J_URL", "")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

    