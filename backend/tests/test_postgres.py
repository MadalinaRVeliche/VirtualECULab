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
    # Require an explicit test URL so the regular test suite can run
    # without PostgreSQL and this test uses a dedicated database.
    url = os.getenv("POSTGRES_TEST_URL")
    if not url:
        pytest.skip(
            "POSTGRES_TEST_URL not set; run against a disposable PostgreSQL database only."
        )

    engine = create_engine(url)
    assert engine.dialect.name == "postgresql"
    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        transaction = connection.begin()

        def override():
            # Route handlers can call commit() normally. Their sessions
            # use savepoints so the outer transaction can roll back test rows.
            with Session(
                bind=connection, join_transaction_mode="create_savepoint"
            ) as session:
                yield session

        # Temporarily replace the SQLite override from conftest.py.
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = override
        try:
            client = TestClient(app)

            # Repeating the same milestone should succeed and leave it marked.
            assert client.post("/modules/4/theory-reviewed").status_code == 200
            assert client.post("/modules/4/theory-reviewed").status_code == 200
            assert client.get("/learning/progress").json()["4"]["theory_reviewed"]

            # Ask for a replacement set and verify that it excludes every
            # question ID from the set the learner was viewing.
            quiz = client.get("/modules/0/quiz").json()
            fresh_quiz = client.get(
                "/modules/0/quiz", params={"previous_session": quiz["session_id"]}
            ).json()
            assert {q["id"] for q in quiz["questions"]}.isdisjoint(
                q["id"] for q in fresh_quiz["questions"]
            )
            from backend.curriculum import MODULES

            # Build a known-correct submission from the server-side bank
            # because the quiz API omits the answer key.
            bank = {q["id"]: q for q in MODULES[0]["quiz_bank"]}
            submission = {
                "session_id": quiz["session_id"],
                "submission_id": str(uuid4()),
                "answers": {
                    q["id"]: bank[q["id"]]["correct"] for q in quiz["questions"]
                },
            }
            result = client.post("/modules/0/quiz", json=submission)
            assert result.status_code == 200, result.text
            assert result.json()["score"] == result.json()["total"] == 10

            # Resend the same payload and submission ID to simulate a retry.
            # Check both the returned result and the number of rows saved.
            assert (
                client.post("/modules/0/quiz", json=submission).json() == result.json()
            )
            assert client.get("/learning/progress").json()["0"]["best_percent"] == 100
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
            # Restore the original dependency and roll back the test data
            # even when an assertion fails.
            if previous:
                app.dependency_overrides[get_db] = previous
            else:
                app.dependency_overrides.pop(get_db, None)
            transaction.rollback()

    engine.dispose()