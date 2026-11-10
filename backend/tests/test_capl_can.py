import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

PROGRAM = """
variables
{
  message 0x123 VehicleSpeed;
}

on key 'a'
{
  VehicleSpeed.dlc = 2;
  VehicleSpeed.byte(0) = 0x10;
  VehicleSpeed.byte(1) = 0x27;
  output(VehicleSpeed);
}
"""


def test_output_transmits_frame_for_matching_key():
    response = client.post(
        "/simulate",
        json={"code": PROGRAM, "event": "key", "key": "a"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["output"] == []
    assert len(result["frames"]) == 1
    assert result["frames"][0]["identifier_hex"] == "0x123"
    assert result["frames"][0]["dlc"] == 2
    assert result["frames"][0]["data_hex"] == "10 27"


def test_start_does_not_transmit_keyboard_message():
    response = client.post(
        "/simulate",
        json={"code": PROGRAM},
    )

    assert response.status_code == 200
    assert response.json() == {"output": [], "frames": []}


def test_assigning_bytes_without_output_does_not_transmit():
    code = PROGRAM.replace("output(VehicleSpeed);", "")

    response = client.post(
        "/simulate",
        json={"code": code, "event": "key", "key": "a"},
    )

    assert response.status_code == 200
    assert response.json()["frames"] == []


def test_each_output_captures_a_separate_snapshot():
    code = PROGRAM.replace(
        "output(VehicleSpeed);",
        """
        output(VehicleSpeed);
        VehicleSpeed.byte(0) = 0x88;
        VehicleSpeed.byte(1) = 0x13;
        output(VehicleSpeed);
        """,
    )

    response = client.post(
        "/simulate",
        json={"code": code, "event": "key", "key": "a"},
    )

    assert response.status_code == 200
    frames = response.json()["frames"]
    assert [frame["data_hex"] for frame in frames] == [
        "10 27",
        "88 13",
    ]


@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        ("VehicleSpeed.dlc = 2;", ""),
        ("VehicleSpeed.dlc = 2;", "VehicleSpeed.dlc = 9;"),
        ("byte(0)", "byte(8)"),
        ("= 0x10;", "= 256;"),
        ("message 0x123", "message 0x800"),
    ],
)
def test_invalid_message_program_is_rejected(original, replacement):
    code = PROGRAM.replace(original, replacement)

    response = client.post(
        "/simulate",
        json={"code": code, "event": "key", "key": "a"},
    )

    assert response.status_code == 400
