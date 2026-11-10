from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


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
    response = client.post(
        "/lessons/1/check",
        json={"code": 'on start { write("Other message"); }'},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False


def test_exercise_rejects_extra_output():
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


def test_lessons_include_both_exercises():
    response = client.get("/lessons")

    assert response.status_code == 200
    lessons = response.json()
    assert [lesson["id"] for lesson in lessons] == [1, 2]
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


def test_second_exercise_rejects_reversed_order():
    response = client.post(
        "/lessons/2/check",
        json={"code": ('on start {write("System ready");write("Starting ECU");}')},
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False
