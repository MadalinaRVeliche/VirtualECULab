from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# These tests cover the original single-handler endpoint used by the
# introductory exercises. The Workbench runtime has its own test coverage.
def test_simulator_returns_message():
    code = 'on start\n{\n  write("Hello, ECU!");\n}'

    response = client.post("/simulate", json={"code": code})

    assert response.status_code == 200
    assert response.json() == {"output": ["Hello, ECU!"]}


def test_simulator_rejects_invalid_code():
    response = client.post("/simulate", json={"code": "abc"})

    assert response.status_code == 400
    assert "detail" in response.json()


def test_simulator_accepts_extra_whitespace():
    code = '\n  on   start  {\n\n write ( "Test" ) ;\n  }\n'

    response = client.post("/simulate", json={"code": code})

    assert response.status_code == 200
    assert response.json() == {"output": ["Test"]}


def test_simulator_rejects_code_outside_event():
    # A valid handler followed by extra code should still be rejected.
    code = 'on start { write("Salut!"); } write("Extra");'

    response = client.post("/simulate", json={"code": code})

    assert response.status_code == 400


def test_simulator_returns_multiple_messages_in_order():
    code = """
    on start
    {
      write("Starting ECU");
      write("System ready");
    }
    """

    response = client.post("/simulate", json={"code": code})

    assert response.status_code == 200
    assert response.json() == {"output": ["Starting ECU", "System ready"]}


def test_simulator_rejects_unsupported_instruction():
    code = 'on start { write("Salut!"); unknown(); }'

    response = client.post("/simulate", json={"code": code})

    assert response.status_code == 400


def test_simulator_accepts_empty_event():
    response = client.post(
        "/simulate",
        json={"code": "on start { }"},
    )

    assert response.status_code == 200
    assert response.json() == {"output": []}


def test_exercise_accepts_correct_output():
    response = client.post(
        "/lessons/1/check",
        json={"code": 'on start { write("ECU ready"); }'},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_exercise_rejects_wrong_output():
    # The submission is valid CAPL, so the API returns a failing verdict
    # with HTTP 200. Invalid CAPL is covered separately as HTTP 400.
    response = client.post(
        "/lessons/1/check",
        json={"code": 'on start { write("Other message"); }'},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False


def test_exercise_rejects_extra_output():
    # Producing the expected line is insufficient if extra lines are emitted.
    response = client.post(
        "/lessons/1/check",
        json={"code": ('on start { write("ECU ready"); write("Extra"); }')},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False


def test_exercise_rejects_invalid_code():
    response = client.post(
        "/lessons/1/check",
        json={"code": "abc"},
    )

    assert response.status_code == 400


def test_exercise_returns_404_for_unknown_lesson():
    response = client.post(
        "/lessons/999/check",
        json={"code": 'on start { write("ECU ready"); }'},
    )

    assert response.status_code == 404


def test_lessons_include_all_exercises():
    response = client.get("/lessons")

    assert response.status_code == 200
    lessons = response.json()
    assert [lesson["id"] for lesson in lessons] == [1, 2, 3]
    assert all(lesson["task"] for lesson in lessons)


def test_second_exercise_accepts_correct_order():
    response = client.post(
        "/lessons/2/check",
        json={"code": ('on start {write("Starting ECU");write("System ready");}')},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert response.json()["output"] == [
        "Starting ECU",
        "System ready",
    ]


def test_correct_answer_saves_progress_once():
    submission = {"code": 'on start { write("ECU ready"); }'}

    # Submit twice to check that completion is stored once per lesson.
    for _ in range(2):
        response = client.post(
            "/lessons/1/check",
            json=submission,
        )
        assert response.status_code == 200
        assert response.json()["passed"] is True

    progress = client.get("/progress")

    assert progress.status_code == 200
    assert progress.json() == {"completed_lesson_ids": [1]}


def test_wrong_answer_does_not_save_progress():
    response = client.post(
        "/lessons/1/check",
        json={"code": 'on start { write("Wrong"); }'},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False
    assert client.get("/progress").json() == {"completed_lesson_ids": []}


def test_second_exercise_rejects_reversed_order():
    response = client.post(
        "/lessons/2/check",
        json={"code": ('on start {write("System ready");write("Starting ECU");}')},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False


def test_keyboard_event_does_not_run_on_start():
    response = client.post(
        "/simulate",
        json={"code": """on key 'a' { write("Pressed"); }"""},
    )

    assert response.status_code == 200
    assert response.json() == {"output": []}


def test_keyboard_event_runs_for_matching_key():
    response = client.post(
        "/simulate",
        json={
            "code": """on key 'a' { write("Pressed"); }""",
            "event": "key",
            "key": "a",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"output": ["Pressed"]}


def test_keyboard_event_ignores_other_keys():
    response = client.post(
        "/simulate",
        json={
            "code": """on key 'a' { write("Pressed"); }""",
            "event": "key",
            "key": "b",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"output": []}


def test_start_event_does_not_run_on_key_press():
    response = client.post(
        "/simulate",
        json={
            "code": 'on start { write("Started"); }',
            "event": "key",
            "key": "a",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"output": []}


def test_invalid_keyboard_body_is_rejected_without_trigger():
    # The parser checks the body even though the default startup event
    # would not execute this keyboard handler.
    response = client.post(
        "/simulate",
        json={"code": "on key 'a' { unknown(); }"},
    )

    assert response.status_code == 400


def test_third_exercise_saves_completion():
    response = client.post(
        "/lessons/3/check",
        json={"code": """on key 'a' { write("Key A pressed"); }"""},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert response.json()["output"] == ["Key A pressed"]
    assert client.get("/progress").json() == {"completed_lesson_ids": [3]}


def test_third_exercise_rejects_start_event():
    # The text matches, but the exercise sends a key event. A startup
    # handler cannot satisfy a requirement tied to that stimulus.
    response = client.post(
        "/lessons/3/check",
        json={"code": 'on start { write("Key A pressed"); }'},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False
    assert client.get("/progress").json() == {"completed_lesson_ids": []}