import pytest
import os
import sqlalchemy as sql
from pathlib import Path
from testcontainers.postgres import PostgresContainer
from fastapi.testclient import TestClient

from randovisual.api.app import app as real_app
from randovisual.api.db import get_engine

postgres = PostgresContainer("postgis/postgis:18-3.6")


def _migrations(migrations_dir="../migrations"):
    """Generate text content from migration files in lexicographic order."""
    base_path = Path(migrations_dir)

    for filepath in sorted(base_path.glob("*.sql")):
        with open(filepath, 'r') as f:
            yield filepath.name, f.read()

@pytest.fixture(scope="module", autouse=True)
def db(request):
    postgres.start()
    request.addfinalizer(lambda: postgres.stop())

    os.environ["DATABASE_URL"] = postgres.get_connection_url(driver="psycopg")
    with get_engine().begin() as conn:
        for filename, migration in _migrations():
            print(f"Executing migration {filename}")
            conn.execute(sql.text(migration))

@pytest.fixture(scope="module")
def app(request):
    client = TestClient(real_app)
    return client


@pytest.fixture()
def conn(request):
    with get_engine().begin() as conn:
        yield conn
