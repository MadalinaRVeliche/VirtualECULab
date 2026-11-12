from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_standard_frame_preview():
    response = client.post(
        "/can/frames/preview",
        json={
            "identifier": 0x123,
            "data": [0x10, 0x27],
        },
    )

    assert response.status_code == 200

    # Verify both the numeric fields used by the app and the formatted
    # hexadecimal strings shown to the learner.
    assert response.json() == {
        "format": "Classical CAN standard data frame",
        "identifier": 0x123,
        "identifier_hex": "0x123",
        "dlc": 2,
        "data": [0x10, 0x27],
        "data_hex": "10 27",
    }


def test_standard_frame_rejects_identifier_above_11_bits():
    # 0x800 is the first value above the standard 11-bit ID range.
    response = client.post(
        "/can/frames/preview",
        json={"identifier": 0x800, "data": [0]},
    )

    assert response.status_code == 422


def test_frame_rejects_value_larger_than_one_byte():
    response = client.post(
        "/can/frames/preview",
        json={"identifier": 0x123, "data": [256]},
    )

    assert response.status_code == 422


def test_classical_can_rejects_nine_payload_bytes():
    response = client.post(
        "/can/frames/preview",
        json={"identifier": 0x123, "data": [0] * 9},
    )

    assert response.status_code == 422


def test_frame_accepts_zero_payload_bytes():
    # An empty payload is valid and should be represented as DLC 0.
    response = client.post(
        "/can/frames/preview",
        json={"identifier": 0x123, "data": []},
    )

    assert response.status_code == 200
    assert response.json()["dlc"] == 0
    assert response.json()["data_hex"] == ""