import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import g

LOCAL_DB_CONFIG = {
    "dbname": "dna_lab",
    "user": "ayushmali",
    "password": "",
    "host": "localhost",
    "port": 5432
}


def get_db():

    if "db" not in g:
        database_url = os.environ.get('DATABASE_URL')

        if database_url:
            g.db = psycopg2.connect(
                database_url,
                sslmode='require', 
                cursor_factory=RealDictCursor
            )
        else:
            g.db = psycopg2.connect(
                **LOCAL_DB_CONFIG,
                cursor_factory=RealDictCursor
            )
            
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()