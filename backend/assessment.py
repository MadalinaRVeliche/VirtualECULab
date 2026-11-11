"""Behavioral checks use deterministic scenarios, never console success claims."""

from backend.engine import Runtime
from backend.lab_tools import (
    ADASRequest,
    E2ERequest,
    SignalSettings,
    adas_result,
    check_e2e,
    decode,
)


def e2e_case(challenge=False):
    if challenge:
        return {
            "max_lost": 1,
            "frames": [
                {"counter": c, "corrupt": bad}
                for c, bad in [
                    (14, False),
                    (0, False),
                    (0, False),
                    (1, True),
                    (1, False),
                    (4, False),
                    (2, False),
                ]
            ],
        }
    return {
        "max_lost": 0,
        "frames": [
            {"counter": c, "corrupt": bad}
            for c, bad in [
                (5, False),
                (6, False),
                (7, False),
                (7, False),
                (8, True),
                (8, False),
            ]
        ],
    }


def adas_cases(challenge=False):
    threshold = 1.5 if challenge else 2.0
    return [
        {
            "distance_m": 15 if challenge else 20,
            "ego_kmh": 72,
            "target_kmh": 36,
            "threshold_s": threshold,
        },
        {"distance_m": 30, "ego_kmh": 72, "target_kmh": 36, "threshold_s": threshold},
        {"distance_m": 10, "ego_kmh": 36, "target_kmh": 72, "threshold_s": threshold},
        {
            "distance_m": 5,
            "ego_kmh": 72,
            "target_kmh": 0,
            "threshold_s": threshold,
            "sensor_valid": False,
        },
    ]


def assess(module_id, code, payload, challenge=False):
    checks = []
    evidence = None

    def check(name, actual, expected):
        checks.append(
            {
                "name": name,
                "passed": actual == expected,
                "actual": actual,
                "expected": expected,
            }
        )

    def run(actions):
        nonlocal evidence
        evidence = Runtime(code).replay(actions)
        return evidence

    if module_id <= 3:
        actions = (
            []
            if module_id != 3
            else [{"type": "key", "key": "b" if challenge else "a"}]
        )
        result = run(actions)
        expected = {
            1: ["ECU booting", "ECU ready"] if challenge else ["ECU ready"],
            2: ["Boot", "Ready", "Running"]
            if challenge
            else ["Starting ECU", "System ready"],
            3: ["Key B pressed"] if challenge else ["Key A pressed"],
        }[module_id]
        check("Exact console sequence", result["output"], expected)
        if module_id == 3:
            check("Startup remains silent", Runtime(code).replay([])["output"], [])
    elif module_id == 4:
        check("Startup does not transmit", run([])["frames"], [])
        frames = run([{"type": "key", "key": "a"}])["frames"]
        expected_data = (
            [[0xC4, 0x09], [0x4C, 0x1D]] if challenge else [[0x10, 0x27], [0x88, 0x13]]
        )
        check(
            "Exact ID, DLC, payload and frame order",
            [(f["identifier"], f["dlc"], f["data"]) for f in frames],
            [(0x123, 2, data) for data in expected_data],
        )
        check(
            "Other keys do not transmit",
            run([{"type": "key", "key": "b"}])["frames"],
            [],
        )
    elif module_id == 5:
        step = 2 if challenge else 1
        frames = run([{"type": "key", "key": "a"}] * 3)["frames"]
        check(
            "Persistent counter frames",
            [(f["identifier"], f["data"]) for f in frames],
            [(0x200, [step * i]) for i in (1, 2, 3)],
        )
        # A fresh replay must initialize rather than continuing a previous measurement.
        check(
            "New measurement resets count",
            run([{"type": "key", "key": "a"}])["frames"][0:1],
            frames[0:1],
        )
        check(
            "Unrelated key leaves counter unchanged",
            [
                f["data"]
                for f in run(
                    [
                        {"type": "key", "key": "a"},
                        {"type": "key", "key": "b"},
                        {"type": "key", "key": "a"},
                    ]
                )["frames"]
            ],
            [[step], [2 * step]],
        )
    elif module_id == 6:
        period = 50 if challenge else 100
        frames = run([{"type": "advance", "ms": 3 * period}])["frames"]
        check(
            "Periodic ID, payload and timestamps",
            [(f["identifier"], f["data"], f["time_ms"]) for f in frames],
            [(0x300, [1], period * i) for i in (1, 2, 3)],
        )
        actions = [
            {"type": "advance", "ms": 3 * period},
            {"type": "key", "key": "s"},
            {"type": "advance", "ms": 2 * period},
            {"type": "key", "key": "r"},
            {"type": "advance", "ms": period},
        ]
        check(
            "Stop cancels and restart uses a fresh delay",
            [f["time_ms"] for f in run(actions)["frames"]],
            [period, 2 * period, 3 * period, 6 * period],
        )
        check(
            "No frame before first deadline",
            run([{"type": "advance", "ms": period - 1}])["frames"],
            [],
        )
        check(
            "Continues beyond the first three periods",
            [
                f["time_ms"]
                for f in run([{"type": "advance", "ms": 7 * period}])["frames"]
            ],
            [period * i for i in range(1, 8)],
        )
    elif module_id == 7:
        timeout = 300 if challenge else 500
        rx = {"type": "rx", "identifier": 0x300, "data": [1]}
        check(
            "Startup timeout",
            run([{"type": "advance", "ms": timeout}])["output"],
            ["Communication timeout"],
        )
        actions = [
            {"type": "advance", "ms": 100},
            rx,
            {"type": "advance", "ms": 100},
            rx,
            {"type": "advance", "ms": timeout - 1},
        ]
        check("No early timeout after rearming", run(actions)["output"], [])
        result = run(actions + [{"type": "advance", "ms": 1}])
        check(
            "Timeout follows last reception",
            result["console"],
            [{"time_ms": 200 + timeout, "text": "Communication timeout"}],
        )
        check("State reports timeout", result["variables"].get("timedOut"), 1)
        result = run(actions + [{"type": "advance", "ms": 1}, rx])
        check("Reception clears timeout state", result["variables"].get("timedOut"), 0)
        result = run(
            [
                {"type": "advance", "ms": 100},
                {"type": "rx", "identifier": 0x301, "data": [1]},
                {"type": "advance", "ms": timeout - 100},
            ]
        )
        check(
            "Unrelated IDs do not postpone timeout",
            result["output"],
            ["Communication timeout"],
        )
        check(
            "Timeout is one-shot during continued silence",
            run([{"type": "advance", "ms": 3 * timeout}])["output"],
            ["Communication timeout"],
        )
        result = run(
            [{"type": "advance", "ms": timeout}, rx, {"type": "advance", "ms": timeout}]
        )
        check(
            "Recovery rearms a new loss deadline",
            [entry["time_ms"] for entry in result["console"]],
            [timeout, 2 * timeout],
        )
    elif module_id == 8:
        settings = SignalSettings.model_validate(payload.get("settings", {}))
        cases = (
            [([0x03, 0xE8], 90), ([0x01, 0xF4], 40), ([0, 0], -10)]
            if challenge
            else [([0x10, 0x27], 100), ([0x88, 0x13], 50), ([0, 0], 0)]
        )
        for data, expected in cases:
            check(
                "Decode " + " ".join(f"{v:02X}" for v in data),
                decode(data, settings)["physical"],
                expected,
            )
    elif module_id == 9:
        rows = check_e2e(E2ERequest.model_validate(e2e_case(challenge)))["rows"]
        check(
            "Integrity and sequence classifications",
            payload.get("predictions", []),
            [r["status"] for r in rows],
        )
        evidence = {"rows": rows}
    elif module_id == 10:
        deadline = 150 if challenge else 100
        check(
            "Event-based response checking selected", payload.get("strategy"), "event"
        )
        check("Requirement deadline configured", payload.get("deadline_ms"), deadline)
        # Candidate predicts fresh response, boundary, late, absent, invalid preconditions.
        check(
            "Verdicts across timing/setup cases",
            payload.get("predictions", []),
            ["PASS", "PASS", "FAIL", "FAIL", "NOT_EXECUTED"],
        )
    elif module_id == 11:
        expected = [
            adas_result(ADASRequest.model_validate(case))["state"]
            for case in adas_cases(challenge)
        ]
        check("Scenario classifications", payload.get("predictions", []), expected)
    else:
        raise ValueError("Unknown module.")
    return {
        "passed": bool(checks) and all(c["passed"] for c in checks),
        "checks": checks,
        "evidence": evidence,
    }
