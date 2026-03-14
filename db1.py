# db.py - Database connection utility for GenoScope
# Uses environment variables for configuration (never hardcode credentials)

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import g

def get_db():
    """
    Get a database connection from the Flask application context.
    Uses DATABASE_URL env var for production (e.g., Neon, Render, Heroku).
    Falls back to local config only in development (via .env.local).
    """
    if 'db' not in g:
        database_url = os.environ.get('DATABASE_URL')

        if database_url:
            # Production / cloud (Neon, etc.) - uses SSL by default
            g.db = psycopg2.connect(
                database_url,
                sslmode='require',
                cursor_factory=RealDictCursor
            )
        else:
            # Local development only - load from .env.local or environment
            # NEVER commit real credentials here!
            from dotenv import load_dotenv
            load_dotenv()  # optional - only if using python-dotenv

            g.db = psycopg2.connect(
                dbname=os.getenv('DB_NAME', 'genoscope_dev'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                cursor_factory=RealDictCursor
            )

    return g.db


def close_db(e=None):
    """Close the database connection at the end of each request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# Optional: Register close_db with Flask app (in app.py or wherever you init app)
# @app.teardown_appcontext
# def teardown_db(exception):
#     close_db()