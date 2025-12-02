import sqlalchemy
import psycopg
import os

DB_CONFIG = {
    "host": "localhost",
    "database": "rusa",
    "user": "rusa",
    "password": "rusa",
    "port": 5432
}

def get_db():
    engine = sqlalchemy.create_engine(os.getenv("DB_URL_SERVER"))
    with engine.begin() as conn:
        yield conn
