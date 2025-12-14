import os

import sqlalchemy


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_engine() -> sqlalchemy.Engine:
    return sqlalchemy.create_engine(get_db_url())


def get_db() -> sqlalchemy.Connection:
    with get_engine().begin() as conn:
        yield conn
