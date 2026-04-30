import pytest
import sqlalchemy
from testcontainers.postgres import PostgresContainer
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Create a temporary SQL container
@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg

@pytest.fixture(scope="session")
def db_engine(pg_container):
    engine = sqlalchemy.create_engine(pg_container.get_connection_url())
    return engine

@pytest.fixture(scope="session", autouse=True)
def setup_schema(db_engine):
   #Create users table to test
    with db_engine.begin() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                email TEXT,
                last_name TEXT,
                description TEXT
            )
        """))

#Mock of Supabase Client into Postgres
@pytest.fixture
def mock_supabase(db_engine):
    #Replace Supabase client with a false that will execute the requests on the fake sql container
    class FakeQuery:
        def __init__(self, table):
            self._table = table
            self._updates = {}
            self._filter_col = None
            self._filter_val = None

        def update(self, data):
            self._updates = data
            return self

        def eq(self, col, val):
            self._filter_col = col
            self._filter_val = val
            return self

        def execute(self):
            set_clause = ", ".join(f"{k} = :{k}" for k in self._updates)
            sql = sqlalchemy.text(
                f"UPDATE {self._table} SET {set_clause} "
                f"WHERE {self._filter_col} = :__filter_val "
                f"RETURNING *"
            )
            params = {**self._updates, "__filter_val": self._filter_val}
            with db_engine.begin() as conn:
                result = conn.execute(sql, params)
                rows = [dict(r._mapping) for r in result.fetchall()]
            response = MagicMock()
            response.data = rows
            return response

    class FakeSupabase:
        def table(self, name):
            return FakeQuery(name)

    return FakeSupabase()

@pytest.fixture
def client(mock_supabase):
    #Inject the mock where it is used in the app and return Test Client
    with patch("routers.users.supabase", mock_supabase):
        from main import app
        yield TestClient(app)

@pytest.fixture
def seed_user(db_engine):
    #Insert a test user and delete it after the test
    user_id = "14998"
    with db_engine.begin() as conn:
        conn.execute(sqlalchemy.text(
            "INSERT INTO users (id, first_name, email, last_name, description) VALUES (:id, :first_name, :email, :last_name, :description)"
        ), {"id": user_id, "first_name": "Alice", "email": "alice@example.com", "last_name": "Dupoirier", "description": "J'aime le poulet"})
    yield user_id
    with db_engine.begin() as conn:
        conn.execute(sqlalchemy.text("DELETE FROM users WHERE id = :id"), {"id": user_id})