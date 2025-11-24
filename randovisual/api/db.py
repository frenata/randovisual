import sqlalchemy
import psycopg

DB_CONFIG = {
    "host": "localhost",
    "database": "rusa",
    "user": "rusa",
    "password": "rusa",
    "port": 5432
}

def get_db():
    engine = sqlalchemy.create_engine("postgresql+psycopg://rusa:rusa@localhost/rusa")
    with engine.begin() as conn:
        yield conn
