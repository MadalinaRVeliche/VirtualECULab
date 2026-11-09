from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_simulator_returns_message():
    code = 'on start\n{\n  write("Salut, ECU!");\n}'

    response = client.post("/simulate", json={"code": code})

    assert response.status_code == 200
    assert response.json() == {"output": ["Salut, ECU!"]}


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
      write("Pornire ECU");
      write("Sistem pregatit");
    }
    """

    response = client.post("/simulate", json={"code": code})

    assert response.status_code == 200
    assert response.json() == {"output": ["Pornire ECU", "Sistem pregatit"]}


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
