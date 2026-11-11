from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.curriculum import MODULES, PERIODIC, SPEED, STATE, WATCHDOG
from backend.engine import Runtime
from backend.lab_tools import crc8
from backend.main import app

client = TestClient(app)


def test_curriculum_hides_quiz_answer_keys_and_covers_all_modules():
    response = client.get("/modules")
    assert response.status_code == 200
    entries = response.json()
    assert [entry["id"] for entry in entries] == list(range(12))
    assert entries[0]["kind"] == "theory"
    assert not entries[0]["challenge"]
    assert all(entry["theory"] and entry["challenge"] for entry in entries[1:])
    assert all("quiz_bank" not in entry for entry in entries)


@pytest.mark.parametrize(
    "identifier,code", [(4, SPEED), (5, STATE), (6, PERIODIC), (7, WATCHDOG)]
)
def test_reference_programs_pass_and_save_practical(identifier, code):
    response = client.post(f"/modules/{identifier}/check", json={"code": code})
    assert response.status_code == 200, response.text
    assert response.json()["passed"] is True
    assert client.get("/learning/progress").json()[str(identifier)][
        "practical_completed"
    ]


@pytest.mark.parametrize(
    "identifier,code",
    [
        (
            4,
            SPEED.replace("0x10", "0xC4")
            .replace("0x27", "0x09")
            .replace("0x88", "0x4C")
            .replace("0x13;", "0x1D;"),
        ),
        (5, STATE.replace("count++;", "count = count + 2;")),
        (6, PERIODIC.replace("100", "50")),
        (7, WATCHDOG.replace("500", "300")),
    ],
)
def test_challenges_have_distinct_behavior_and_progress(identifier, code):
    response = client.post(
        f"/modules/{identifier}/check", json={"code": code, "challenge": True}
    )
    assert response.status_code == 200, response.text
    assert response.json()["passed"] is True
    record = client.get("/learning/progress").json()[str(identifier)]
    assert record["challenge_completed"] and not record["practical_completed"]


@pytest.mark.parametrize(
    "change",
    [
        lambda code: code.replace("output(VehicleSpeed);", ""),
        lambda code: code.replace("0x123", "0x124"),
        lambda code: code.replace("dlc = 2", "dlc = 3"),
        lambda code: code.replace("0x10", "0x11"),
        lambda code: code.replace("on key 'a'", "on start"),
        lambda code: code.replace("0x10", "0x88").replace("0x27", "0x13"),
    ],
)
def test_transmission_checker_rejects_wrong_frame_behavior(change):
    response = client.post("/modules/4/check", json={"code": change(SPEED)})
    assert response.status_code == 200
    assert not response.json()["passed"]


def test_logging_success_does_not_pass_transmission():
    response = client.post(
        "/modules/4/check",
        json={"code": "on key 'a' { write(\"100 then 50 km/h sent\"); }"},
    )
    assert response.status_code == 200
    assert not response.json()["passed"]


@pytest.mark.parametrize(
    "identifier,code",
    [
        (5, STATE.replace("count++;", "count = 1;")),
        (
            6,
            PERIODIC.replace(
                "  setTimer(heartbeat, 100);\n}\non key", "\n}\non key", 1
            ),
        ),
        (6, PERIODIC.replace("cancelTimer(heartbeat);", 'write("Stopped");')),
        (
            7,
            WATCHDOG.replace(
                "  setTimer(watchdog, 500);\n}\non timer", "\n}\non timer", 1
            ),
        ),
        (7, WATCHDOG.replace("timedOut = 0;\n  setTimer", 'write("Rx");\n  setTimer')),
    ],
)
def test_behavioral_checkers_reject_broken_solutions(identifier, code):
    response = client.post(f"/modules/{identifier}/check", json={"code": code})
    assert response.status_code == 200, response.text
    assert not response.json()["passed"]


def test_timer_and_receive_boundary_is_explicit():
    response = client.post(
        "/lab/run",
        json={
            "code": WATCHDOG,
            "actions": [
                {"type": "advance", "ms": 500},
                {"type": "rx", "identifier": 0x300, "data": [1]},
            ],
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["console"] == [{"time_ms": 500, "text": "Communication timeout"}]
    assert result["variables"]["timedOut"] == 0
    assert result["timers"]["watchdog"] == 1000


def test_timer_rearm_replaces_old_deadline():
    code = 'variables { msTimer t; } on start { setTimer(t,100); setTimer(t,200); } on timer t { write("T"); }'
    result = Runtime(code).replay([{"type": "advance", "ms": 150}])
    assert result["output"] == []
    assert result["timers"]["t"] == 200
    result = Runtime(code).replay([{"type": "advance", "ms": 200}])
    assert result["console"] == [{"time_ms": 200, "text": "T"}]


def test_equal_deadline_timers_use_schedule_order():
    code = 'variables { msTimer a; msTimer b; } on start { setTimer(b,10); setTimer(a,10); } on timer a { write("A"); } on timer b { write("B"); }'
    assert Runtime(code).replay([{"type": "advance", "ms": 10}])["output"] == ["B", "A"]


def test_output_snapshots_and_no_automatic_loopback():
    code = STATE + '\non message 0x200 { write("Loopback"); }'
    result = Runtime(code).replay([{"type": "key", "key": "a"}] * 3)
    assert [f["data"] for f in result["frames"]] == [[1], [2], [3]]
    assert result["output"] == []


def test_this_byte_and_if_else_on_reception():
    code = 'on message 0x300 { if(this.dlc > 0 && this.byte(0) == 1) { write("Valid"); } else { write("Other"); } }'
    result = Runtime(code).replay(
        [
            {"type": "rx", "identifier": 0x300, "data": []},
            {"type": "rx", "identifier": 0x300, "data": [1]},
        ]
    )
    assert result["output"] == ["Other", "Valid"]
    assert all(frame["direction"] == "Rx" for frame in result["frames"])


@pytest.mark.parametrize(
    "code",
    [
        "variables { int x; int x; } on start {}",
        "on start {} on start {}",
        "on key 'a' { unknown(); }",
        "on key 'a' { x = 1; }",
        "on timer t {}",
        "on start { write(this.byte(0)); }",
        'on start { __import__("os"); }',
        "on start { while(1) {} }",
        "variables { message 0x800 m; } on start {}",
        "variables { msTimer t; } on start { setTimer(t,0); }",
        "variables { byte b; } on start { b = 256; }",
        "variables { int n; } on start { n = 1 / 0; }",
        "variables { message 0x123 m; } on start { output(m); }",
        "variables { message 0x123 m; } on start { m.byte(8) = 1; }",
        "variables { message 0x123 m; } on start { m.dlc = 9; }",
    ],
)
def test_invalid_programs_are_rejected(code):
    response = client.post("/lab/run", json={"code": code})
    assert response.status_code == 400, response.text


def test_reception_rejects_out_of_dlc_read():
    response = client.post(
        "/lab/run",
        json={
            "code": "variables { int x; } on message 0x300 { x = this.byte(1); }",
            "actions": [{"type": "rx", "identifier": 0x300, "data": [1]}],
        },
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "actions",
    [
        [{"type": "advance", "ms": -1}],
        [{"type": "key", "key": "ab"}],
        [{"type": "rx", "identifier": 2048, "data": []}],
        [{"type": "rx", "identifier": 1, "data": [256]}],
        [{"type": "advance", "ms": 1}] * 201,
    ],
)
def test_invalid_actions_are_rejected(actions):
    assert (
        client.post(
            "/lab/run", json={"code": "on start {}", "actions": actions}
        ).status_code
        == 422
    )


def test_runtime_budget_prevents_timer_runaway():
    code = "variables { msTimer t; } on start { setTimer(t,1); } on timer t { setTimer(t,1); }"
    response = client.post(
        "/lab/run", json={"code": code, "actions": [{"type": "advance", "ms": 60000}]}
    )
    assert response.status_code == 400
    assert "budget" in response.json()["detail"]


def test_time_span_is_bounded():
    response = client.post(
        "/lab/run",
        json={
            "code": "on start {}",
            "actions": [{"type": "advance", "ms": 60000}, {"type": "advance", "ms": 1}],
        },
    )
    assert response.status_code == 400


def test_theory_review_is_idempotent_and_not_practical_completion():
    for _ in range(2):
        assert client.post("/modules/8/theory-reviewed").status_code == 200
    progress = client.get("/learning/progress").json()["8"]
    assert progress["theory_reviewed"] and not progress["practical_completed"]
    assert progress["quiz_attempts"] == 0


def quiz_answers(module_id, quiz):
    bank = {q["id"]: q for q in MODULES[module_id]["quiz_bank"]}
    return {q["id"]: bank[q["id"]]["correct"] for q in quiz["questions"]}


def submit_quiz(module_id, quiz, answers, identifier=None):
    return client.post(
        f"/modules/{module_id}/quiz",
        json={
            "session_id": quiz["session_id"],
            "submission_id": identifier or str(uuid4()),
            "answers": answers,
        },
    )


@pytest.mark.parametrize("module_id", range(12))
def test_quiz_grades_from_server_bank_and_saves_history(module_id):
    quiz = client.get(f"/modules/{module_id}/quiz").json()
    assert len(quiz["questions"]) == 10
    next_quiz = client.get(
        f"/modules/{module_id}/quiz", params={"previous_session": quiz["session_id"]}
    ).json()
    assert len(next_quiz["questions"]) == 10
    assert {q["id"] for q in quiz["questions"]}.isdisjoint(
        q["id"] for q in next_quiz["questions"]
    )
    assert all(
        "correct" not in question and "explanation" not in question
        for question in quiz["questions"]
    )
    answers = quiz_answers(module_id, quiz)
    response = submit_quiz(module_id, quiz, answers)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["score"] == result["total"] == len(answers)
    assert all(item["explanation"] for item in result["feedback"])
    progress = client.get("/learning/progress").json()[str(module_id)]
    assert progress["best_percent"] == 100 and progress["quiz_attempts"] == 1
    assert not progress["practical_completed"]
    assert len(client.get(f"/modules/{module_id}/quiz-history").json()) == 1


@pytest.mark.parametrize("module_id", range(12))
def test_quiz_rotates_through_unseen_prompts_before_recycling(module_id):
    def prompt_key(question):
        return " ".join(question["prompt"].casefold().split())

    bank = MODULES[module_id]["quiz_bank"]
    unseen = {prompt_key(question) for question in bank}
    assert len(unseen) == len(bank) >= 20
    assert len({question["id"] for question in bank}) == len(bank)
    assert all(
        len(set(question["options"])) == len(question["options"]) for question in bank
    )
    previous = set()
    for _ in range(4):
        response = client.get(f"/modules/{module_id}/quiz")
        assert response.status_code == 200
        current = {prompt_key(question) for question in response.json()["questions"]}
        assert len(current) == 10
        assert previous.isdisjoint(current)
        assert len(current & unseen) == min(10, len(unseen))
        unseen -= current
        previous = current


def test_quiz_deduplicates_prompt_even_if_bank_ids_differ(monkeypatch):
    bank = MODULES[1]["quiz_bank"]
    question = bank[0]
    copies = [
        {**question, "id": f"copy-{i}", "prompt": "  " + question["prompt"].upper()}
        for i in range(20)
    ]
    monkeypatch.setitem(MODULES[1], "quiz_bank", bank + copies)
    response = client.get("/modules/1/quiz")
    assert response.status_code == 200
    assert all(not q["id"].startswith("copy-") for q in response.json()["questions"])


def test_quiz_retry_is_idempotent_but_conflicting_answers_are_rejected():
    quiz = client.get("/modules/1/quiz").json()
    answers = quiz_answers(1, quiz)
    identifier = str(uuid4())
    first = submit_quiz(1, quiz, answers, identifier)
    assert submit_quiz(1, quiz, answers, identifier).json() == first.json()
    missed = quiz["questions"][0]
    answers[missed["id"]] = (answers[missed["id"]] + 1) % len(missed["options"])
    result = submit_quiz(1, quiz, answers).json()
    assert result["score"] == 9
    assert client.get("/learning/progress").json()["1"]["missed_topics"] == [
        missed["topic"]
    ]
    revision = client.get("/modules/1/quiz?revision=true").json()
    assert revision["questions"][0]["id"] == missed["id"]
    submit_quiz(1, revision, quiz_answers(1, revision))
    assert client.get("/learning/progress").json()["1"]["missed_topics"] == []


def test_unknown_module_returns_404():
    assert client.get("/modules/999/quiz").status_code == 404
    assert client.post("/modules/999/check", json={}).status_code == 404


@pytest.mark.parametrize(
    "settings,expected", [({}, 100), ({"byte_order": "big"}, 41.35)]
)
def test_signal_decoder(settings, expected):
    response = client.post(
        "/tools/decode", json={"data": [0x10, 0x27], "settings": settings}
    )
    assert response.status_code == 200
    assert response.json()["physical"] == expected


def test_signal_short_payload_and_invalid_definition():
    assert client.post("/tools/decode", json={"data": [1]}).status_code == 400
    assert (
        client.post(
            "/tools/decode", json={"data": [1, 2], "settings": {"factor": 0}}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/tools/decode",
            json={"data": [1, 2], "settings": {"start_byte": 7, "length": 2}},
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "challenge,settings",
    [(False, {}), (True, {"byte_order": "big", "factor": 0.1, "offset": -10})],
)
def test_signal_config_checker_uses_several_values(challenge, settings):
    response = client.post(
        "/modules/8/check",
        json={"challenge": challenge, "payload": {"settings": settings}},
    )
    assert response.status_code == 200
    assert response.json()["passed"]
    assert not client.post(
        "/modules/8/check", json={"payload": {"settings": {"byte_order": "big"}}}
    ).json()["passed"]


def test_crc_has_known_check_vector():
    assert crc8(b"123456789") == 0x4B


def test_e2e_wraparound_loss_and_rejected_baseline():
    response = client.post(
        "/tools/e2e",
        json={
            "max_lost": 1,
            "frames": [
                {"counter": 15},
                {"counter": 0},
                {"counter": 0},
                {"counter": 2, "corrupt": True},
                {"counter": 2},
                {"counter": 6},
                {"counter": 3},
            ],
        },
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert [r["status"] for r in rows] == [
        "INITIAL",
        "OK",
        "REPEATED",
        "WRONG_CRC",
        "OK_SOME_LOST",
        "WRONG_SEQUENCE",
        "OK",
    ]
    assert [r["accepted_counter"] for r in rows] == [15, 0, 0, 0, 2, 2, 3]


@pytest.mark.parametrize("challenge", [False, True])
def test_e2e_assessment_checks_predictions(challenge):
    case = client.get(f"/modules/9/scenarios?challenge={str(challenge).lower()}").json()
    rows = client.post("/tools/e2e", json=case).json()["rows"]
    predictions = [row["status"] for row in rows]
    assert client.post(
        "/modules/9/check",
        json={"challenge": challenge, "payload": {"predictions": predictions}},
    ).json()["passed"]
    predictions[0] = "OK"
    assert not client.post(
        "/modules/9/check",
        json={"challenge": challenge, "payload": {"predictions": predictions}},
    ).json()["passed"]


@pytest.mark.parametrize("time,expected", [(80, "PASS"), (100, "PASS"), (101, "FAIL")])
def test_verdict_deadline_boundaries(time, expected):
    assert (
        client.post(
            "/tools/verdict",
            json={
                "deadline_ms": 100,
                "observations": [{"time_ms": time, "state": "ACTIVE"}],
            },
        ).json()["verdict"]
        == expected
    )


def test_verdict_missing_response_and_invalid_setup():
    assert client.post("/tools/verdict", json={}).json()["verdict"] == "FAIL"
    assert (
        client.post("/tools/verdict", json={"ready": False}).json()["verdict"]
        == "NOT_EXECUTED"
    )
    assert (
        client.post("/tools/verdict", json={"command_sent": False}).json()["verdict"]
        == "NOT_EXECUTED"
    )


@pytest.mark.parametrize("challenge,deadline", [(False, 100), (True, 150)])
def test_testbench_assessment(challenge, deadline):
    payload = {
        "strategy": "event",
        "deadline_ms": deadline,
        "predictions": ["PASS", "PASS", "FAIL", "FAIL", "NOT_EXECUTED"],
    }
    assert client.post(
        "/modules/10/check", json={"challenge": challenge, "payload": payload}
    ).json()["passed"]
    payload["strategy"] = "immediate"
    assert not client.post(
        "/modules/10/check", json={"challenge": challenge, "payload": payload}
    ).json()["passed"]


@pytest.mark.parametrize(
    "payload,state",
    [
        ({}, "BRAKE_REQUEST"),
        ({"target_kmh": 100}, "MONITORING"),
        ({"obstacle_in_path": False}, "MONITORING"),
        ({"sensor_valid": False}, "DEGRADED"),
        ({"enabled": False}, "OFF"),
        ({"mode": "ACC"}, "ACTIVE"),
        ({"mode": "ACC", "brake_pressed": True}, "OVERRIDDEN"),
    ],
)
def test_adas_explicit_rule(payload, state):
    response = client.post("/tools/adas", json=payload)
    assert response.status_code == 200
    assert response.json()["state"] == state


@pytest.mark.parametrize("challenge", [False, True])
def test_adas_classification_exercise(challenge):
    predictions = ["BRAKE_REQUEST", "MONITORING", "MONITORING", "DEGRADED"]
    assert client.post(
        "/modules/11/check",
        json={"challenge": challenge, "payload": {"predictions": predictions}},
    ).json()["passed"]
    predictions[0] = "MONITORING"
    assert not client.post(
        "/modules/11/check",
        json={"challenge": challenge, "payload": {"predictions": predictions}},
    ).json()["passed"]


def test_arithmetic_precedence_short_circuit_and_c_integer_division():
    code = """variables { int a; int b; int c; int d; int e; }
    on start { a = 2 + 3 * 4; b = -7 / 3; c = -7 % 3;
       d = 0 && 1 / 0; e = 1 || 1 / 0;
       if (a == 14) { write("Precedence OK"); } else { write("Bad"); }
    }"""
    result = Runtime(code).replay([])
    assert result["variables"] == {"a": 14, "b": -2, "c": -1, "d": 0, "e": 1}
    assert result["output"] == ["Precedence OK"]


def test_explicit_modulo_counter_wraparound():
    code = """variables { int counter = 15; message 0x200 Status; }
    on start { Status.dlc = 1; }
    on key 'a' { counter = (counter + 1) % 16; Status.byte(0) = counter; output(Status); }"""
    result = Runtime(code).replay([{"type": "key", "key": "a"}] * 2)
    assert [frame["data"] for frame in result["frames"]] == [[0], [1]]


def test_failed_check_does_not_erase_existing_completion():
    assert client.post("/modules/4/check", json={"code": SPEED}).json()["passed"]
    assert not client.post("/modules/4/check", json={"code": "on start {}"}).json()[
        "passed"
    ]
    assert client.get("/learning/progress").json()["4"]["practical_completed"]


def test_first_bad_crc_does_not_establish_baseline():
    rows = client.post(
        "/tools/e2e",
        json={
            "frames": [
                {"counter": 7, "corrupt": True},
                {"counter": 10},
                {"counter": 11},
            ]
        },
    ).json()["rows"]
    assert [row["status"] for row in rows] == ["WRONG_CRC", "INITIAL", "OK"]
    assert rows[0]["accepted_counter"] is None


def test_teaching_e2e_data_leaves_room_for_counter_and_crc():
    response = client.post(
        "/tools/e2e", json={"frames": [{"counter": 0, "data": [0] * 7}]}
    )
    assert response.status_code == 422


def test_general_theory_has_no_lab_and_ai_generation_is_unavailable():
    assert client.post("/modules/0/check", json={}).status_code == 404
    assert client.post("/modules/1/quiz/generate", json={}).status_code == 404


def test_course_quiz_draws_from_all_topics_without_repeating_until_pool_is_used():
    course = MODULES[0]["quiz_bank"]
    assert len(course) >= 200
    assert all(
        any(q["id"].startswith(f"lesson-{identifier}-") for q in course)
        for identifier in range(1, 12)
    )
    seen = set()
    for _ in range(len(course) // 10):
        response = client.get("/modules/0/quiz")
        assert response.status_code == 200
        questions = {question["id"] for question in response.json()["questions"]}
        assert len(questions) == 10
        assert seen.isdisjoint(questions)
        seen |= questions


def test_workbench_relay_reports_raw_receive_and_transmit_at_virtual_time():
    code = """
    variables { message 0x123 VehicleSpeed; }
    on start { VehicleSpeed.dlc = 2; write("Speed relay ready"); }
    on message 0x120 {
      VehicleSpeed.byte(0) = this.byte(0);
      VehicleSpeed.byte(1) = this.byte(1);
      output(VehicleSpeed);
    }
    """
    response = client.post(
        "/lab/run",
        json={
            "code": code,
            "actions": [
                {"type": "rx", "identifier": 0x120, "data": [0x10, 0x27]},
                {"type": "advance", "ms": 100},
                {"type": "rx", "identifier": 0x120, "data": [0x88, 0x13]},
            ],
        },
    )
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["time_ms"] == 100
    assert run["console"] == [{"time_ms": 0, "text": "Speed relay ready"}]
    assert [
        (frame["time_ms"], frame["direction"], frame["identifier"], frame["data"])
        for frame in run["frames"]
    ] == [
        (0, "Rx", 0x120, [0x10, 0x27]),
        (0, "Tx", 0x123, [0x10, 0x27]),
        (100, "Rx", 0x120, [0x88, 0x13]),
        (100, "Tx", 0x123, [0x88, 0x13]),
    ]
