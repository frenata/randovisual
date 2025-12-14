import sqlalchemy
import os

def get_db_url():
    url = os.getenv("DATABASE_URL")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

def get_db():
    engine = sqlalchemy.create_engine(get_db_url())
    with engine.begin() as conn:
        yield conn


