import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app


@pytest.fixture(autouse=True)
def isolated_database():
    # Create a fresh in-memory database for each test. StaticPool keeps
    # one connection so schema creation and API requests see the same tables.
    # TestClient can handle requests on a different thread from setup.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(test_engine)

    def override_get_db():
        with Session(test_engine) as session:
            yield session

    # Routes that depend on get_db receive a test session instead of
    # connecting to the PostgreSQL database configured for the app.
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield
    finally:
        # Remove the override and close the connection even if the test fails.
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()