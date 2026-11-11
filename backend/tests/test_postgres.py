"""Opt-in integration check. CI supplies its disposable PostgreSQL service."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.database import Base, get_db
from backend.main import app


def test_postgres_persists_learning_and_quiz_records():
    url = os.getenv("POSTGRES_TEST_URL")
    if not url:
        pytest.skip(
            "POSTGRES_TEST_URL not set; run against a disposable PostgreSQL database only."
        )
    # Never drop tables or touch an existing learner's IDs. Use rollback-scoped data.
    engine = create_engine(url)
    assert engine.dialect.name == "postgresql"
    Base.metadata.create_all(engine)
    with engine.connect() as connection:
        transaction = connection.begin()

        def override():
            with Session(
                bind=connection, join_transaction_mode="create_savepoint"
            ) as session:
                yield session

        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = override
        try:
            client = TestClient(app)
            assert client.post("/modules/4/theory-reviewed").status_code == 200
            assert client.post("/modules/4/theory-reviewed").status_code == 200
            assert client.get("/learning/progress").json()["4"]["theory_reviewed"]
            quiz = client.get("/modules/1/quiz").json()
            from backend.curriculum import MODULES

            bank = {q["id"]: q for q in MODULES[1]["quiz_bank"]}
            submission = {
                "session_id": quiz["session_id"],
                "submission_id": str(uuid4()),
                "answers": {
                    q["id"]: bank[q["id"]]["correct"] for q in quiz["questions"]
                },
            }
            result = client.post("/modules/1/quiz", json=submission)
            assert result.status_code == 200, result.text
            assert result.json()["score"] == 5
            assert (
                client.post("/modules/1/quiz", json=submission).json() == result.json()
            )
            assert client.get("/learning/progress").json()["1"]["best_percent"] == 100
            assert (
                connection.execute(
                    text(
                        "SELECT count(*) FROM quiz_attempts WHERE submission_id = :id"
                    ),
                    {"id": submission["submission_id"]},
                ).scalar_one()
                == 1
            )
        finally:
            if previous:
                app.dependency_overrides[get_db] = previous
            else:
                app.dependency_overrides.pop(get_db, None)
            transaction.rollback()
    engine.dispose()
