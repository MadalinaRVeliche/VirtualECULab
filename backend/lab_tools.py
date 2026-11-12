"""Transparent, bounded teaching tools; not OEM control or AUTOSAR implementations."""

import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Byte = Annotated[int, Field(strict=True, ge=0, le=255)]


class SignalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_byte: int = Field(default=0, ge=0, le=7)
    length: int = Field(default=2, ge=1, le=4)
    byte_order: Literal["little", "big"] = "little"
    factor: float = Field(default=0.01, gt=0, le=10000, allow_inf_nan=False)
    offset: float = Field(default=0, ge=-100000, le=100000, allow_inf_nan=False)

    @model_validator(mode="after")
    def bounds(self):
        # Both fields can be valid on their own while their combination
        # places part of the signal outside the eight-byte payload.
        if self.start_byte + self.length > 8:
            raise ValueError("Signal exceeds the Classical CAN payload.")
        return self


def decode(data, settings):
    # This backend exercise decodes an unsigned, byte-aligned speed signal
    # from explicit settings. The Workbench DBC parser lives in the frontend.
    end = settings.start_byte + settings.length
    if end > len(data):
        raise ValueError("Payload is too short for the configured signal.")

    # Extract the raw integer in the configured byte order, then apply
    # the factor and offset to obtain the physical value.
    raw = int.from_bytes(bytes(data[settings.start_byte : end]), settings.byte_order)
    return {
        "raw": raw,
        "physical": round(raw * settings.factor + settings.offset, 8),
        "unit": "km/h",
    }


class DecodeRequest(BaseModel):
    data: list[Byte] = Field(max_length=8)
    settings: SignalSettings = Field(default_factory=SignalSettings)


def crc8(data):
    """CRC-8/SAE-J1850 parameters; our input layout is explicitly non-AUTOSAR."""
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            # Apply the polynomial when the outgoing high bit is set.
            # Mask after each shift to keep the CRC register eight bits wide.
            crc = ((crc << 1) ^ (0x1D if crc & 0x80 else 0)) & 0xFF
    return crc ^ 0xFF


class E2EFrame(BaseModel):
    counter: int = Field(ge=0, le=15, strict=True)
    data: list[Byte] = Field(default_factory=lambda: [0x10, 0x27], max_length=6)
    corrupt: bool = False
    crc: Byte | None = None


class E2ERequest(BaseModel):
    data_id: int = Field(default=0x123, ge=0, le=65535)
    max_lost: int = Field(default=0, ge=0, le=3)
    frames: list[E2EFrame] = Field(min_length=1, max_length=100)


def check_e2e(request):
    accepted = None
    rows = []
    for frame in request.frames:
        # This teaching profile feeds the CRC with the Data ID high byte,
        # Data ID low byte, counter, and payload in that order.
        expected = crc8(
            [request.data_id >> 8, request.data_id & 255, frame.counter, *frame.data]
        )

        # Scenario inputs may supply a received CRC explicitly. Otherwise
        # use the calculated value and optionally flip one bit to simulate a fault.
        received = expected if frame.crc is None else frame.crc
        if frame.corrupt:
            received ^= 1

        # Compare against the last accepted counter. Modulo 16 makes
        # the wrap from 15 to 0 a normal step of one.
        delta = None if accepted is None else (frame.counter - accepted) % 16
        if received != expected:
            status = "WRONG_CRC"
        elif accepted is None:
            status = "INITIAL"
        elif delta == 0:
            status = "REPEATED"
        elif delta == 1:
            status = "OK"
        elif delta <= request.max_lost + 1:
            # A step of two means one intermediate frame was missed.
            status = "OK_SOME_LOST"
        else:
            status = "WRONG_SEQUENCE"

        # A rejected frame must leave the reference counter intact so
        # subsequent frames are still checked against the last accepted one.
        if status in {"INITIAL", "OK", "OK_SOME_LOST"}:
            accepted = frame.counter
        rows.append(
            {
                "counter": frame.counter,
                "status": status,
                "delta": delta,
                "expected_crc": f"{expected:02X}",
                "received_crc": f"{received:02X}",
                "accepted_counter": accepted,
            }
        )
    return {
        "profile": "Teaching profile: modulo 16, NOT an AUTOSAR E2E profile",
        "rows": rows,
    }


class Observation(BaseModel):
    time_ms: int = Field(ge=0, le=60000)
    state: Literal["INACTIVE", "ACTIVE"]


class VerdictRequest(BaseModel):
    deadline_ms: int = Field(default=100, ge=1, le=5000)
    ready: bool = True
    command_sent: bool = True
    observations: list[Observation] = Field(default_factory=list, max_length=100)


def check_verdict(request):
    # Classify an invalid test setup separately from a valid test
    # whose expected response was missing or late.
    if not request.ready or not request.command_sent:
        return {
            "verdict": "NOT_EXECUTED",
            "response_ms": None,
            "reason": "Preconditions or stimulus are missing; no valid behavior test was executed.",
        }

    # The caller supplies observations relative to the stimulus. Use the
    # earliest ACTIVE timestamp regardless of the order in the input list.
    # A response exactly at the deadline passes.
    active = sorted(o.time_ms for o in request.observations if o.state == "ACTIVE")
    first = active[0] if active else None
    passed = first is not None and first <= request.deadline_ms
    return {
        "verdict": "PASS" if passed else "FAIL",
        "response_ms": first,
        "reason": "Fresh ACTIVE observed within deadline."
        if passed
        else "No fresh ACTIVE observed within deadline.",
    }


class ADASRequest(BaseModel):
    mode: Literal["AEB", "ACC"] = "AEB"
    distance_m: float = Field(default=20, ge=0, le=10000, allow_inf_nan=False)
    ego_kmh: float = Field(default=72, ge=0, le=300, allow_inf_nan=False)
    target_kmh: float = Field(default=36, ge=0, le=300, allow_inf_nan=False)
    threshold_s: float = Field(default=2, gt=0, le=10, allow_inf_nan=False)
    obstacle_in_path: bool = True
    sensor_valid: bool = True
    brake_pressed: bool = False
    enabled: bool = True


def adas_result(request):
    # Assume constant speeds. Convert the relative speed to m/s so
    # distance in meters divided by closing speed gives TTC in seconds.
    # A zero or negative closing speed yields no finite TTC in this model.
    closing = (request.ego_kmh - request.target_kmh) / 3.6
    ttc = request.distance_m / closing if closing > 0 else None

    # Evaluate the initial state in priority order: disabled, sensor
    # fault, driver override in ACC, then the default for the selected mode.
    if not request.enabled:
        state = "OFF"
    elif not request.sensor_valid:
        state = "DEGRADED"
    elif request.mode == "ACC" and request.brake_pressed:
        state = "OVERRIDDEN"
    elif request.mode == "ACC":
        state = "ACTIVE"
    else:
        state = "MONITORING"

    # Only the simplified AEB path can request braking. It must be
    # monitoring, see an obstacle in its path, and meet the TTC threshold.
    braking = (
        request.mode == "AEB"
        and state == "MONITORING"
        and request.obstacle_in_path
        and ttc is not None
        and ttc <= request.threshold_s
    )
    if braking:
        state = "BRAKE_REQUEST"
    return {
        "state": state,
        "brake_request": bool(braking),
        "ttc_s": round(ttc, 6) if ttc is not None and math.isfinite(ttc) else None,
        "closing_mps": round(closing, 6),
        "model": "Constant-velocity offline teaching model; not a production ADAS controller.",
    }