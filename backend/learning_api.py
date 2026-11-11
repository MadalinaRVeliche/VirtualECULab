import random
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.assessment import adas_cases, assess, e2e_case
from backend.curriculum import MODULES, public_modules
from backend.database import get_db
from backend.engine import Runtime, SimulationError
from backend.lab_tools import (
    ADASRequest,
    DecodeRequest,
    E2ERequest,
    VerdictRequest,
    adas_result,
    check_e2e,
    check_verdict,
    decode,
)
from backend.models import LearningMilestone, LessonProgress, QuizAttempt, QuizSession

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]


def require_module(identifier):
    if identifier not in MODULES:
        raise HTTPException(404, "Module not found.")
    return MODULES[identifier]


def save_once(db, instance):
    table = instance.__table__
    values = {
        column.name: getattr(instance, column.name) for column in table.primary_key
    }
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise HTTPException(500, "Unsupported database dialect.")
    db.execute(insert(table).values(**values).on_conflict_do_nothing())
    db.commit()


class KeyAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["key"]
    key: str = Field(min_length=1, max_length=1)


class AdvanceAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["advance"]
    ms: int = Field(ge=0, le=60000, strict=True)


class RxAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["rx"]
    identifier: int = Field(ge=0, le=0x7FF, strict=True)
    data: list[Annotated[int, Field(ge=0, le=255, strict=True)]] = Field(max_length=8)


Action = Annotated[KeyAction | AdvanceAction | RxAction, Field(discriminator="type")]


class LabRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20000)
    actions: list[Action] = Field(default_factory=list, max_length=200)


@router.get("/modules")
def get_modules():
    return public_modules()


@router.post("/lab/run")
def run_lab(request: LabRequest):
    try:
        return Runtime(request.code).replay([a.model_dump() for a in request.actions])
    except (SimulationError, RecursionError) as exc:
        detail = (
            str(exc)
            if isinstance(exc, SimulationError)
            else "Program nesting is too deep."
        )
        raise HTTPException(400, detail) from exc


class ModuleSubmission(BaseModel):
    code: str = Field(default="", max_length=20000)
    payload: dict = Field(default_factory=dict)
    challenge: bool = False


@router.post("/modules/{module_id}/check")
def check_module(module_id: int, request: ModuleSubmission, db: DB):
    require_module(module_id)
    try:
        result = assess(module_id, request.code, request.payload, request.challenge)
    except (ValueError, RecursionError, KeyError) as exc:
        detail = (
            str(exc)
            if isinstance(exc, ValueError) and not isinstance(exc, ValidationError)
            else "Invalid lab configuration or unsupported program. Check the documented subset."
        )
        raise HTTPException(400, detail) from exc
    if result["passed"]:
        if request.challenge:
            save_once(db, LearningMilestone(module_id=module_id, kind="challenge"))
        else:
            save_once(db, LessonProgress(lesson_id=module_id))
    result["message"] = (
        "Correct! You completed the challenge."
        if result["passed"] and request.challenge
        else "Correct! You completed the exercise."
        if result["passed"]
        else "Not yet. Inspect the scenario evidence below."
    )
    return result


@router.post("/modules/{module_id}/theory-reviewed")
def review_theory(module_id: int, db: DB):
    require_module(module_id)
    save_once(db, LearningMilestone(module_id=module_id, kind="theory"))
    return {"reviewed": True}


@router.get("/learning/progress")
def learning_progress(db: DB):
    milestones = db.scalars(select(LearningMilestone)).all()
    attempts = db.scalars(select(QuizAttempt).order_by(QuizAttempt.id)).all()
    practical = list(db.scalars(select(LessonProgress.lesson_id)).all())
    result = {}
    for identifier in MODULES:
        history = [a for a in attempts if a.module_id == identifier]
        missed = {}
        for attempt in history:
            for answer in attempt.result["feedback"]:
                if answer["correct"]:
                    missed.pop(answer["id"], None)
                else:
                    missed[answer["id"]] = answer["topic"]
        result[str(identifier)] = {
            "theory_reviewed": any(
                m.module_id == identifier and m.kind == "theory" for m in milestones
            ),
            "practical_completed": identifier in practical,
            "challenge_completed": any(
                m.module_id == identifier and m.kind == "challenge" for m in milestones
            ),
            "quiz_attempts": len(history),
            "best_percent": max(
                (round(a.score / a.total * 100) for a in history), default=None
            ),
            "missed_topics": sorted(set(missed.values())),
        }
    return result


@router.get("/modules/{module_id}/quiz")
def new_quiz(module_id: int, db: DB, revision: bool = False):
    module = require_module(module_id)
    bank = list(module["quiz_bank"])
    random.SystemRandom().shuffle(bank)
    if revision:
        attempts = db.scalars(
            select(QuizAttempt)
            .where(QuizAttempt.module_id == module_id)
            .order_by(QuizAttempt.id)
        ).all()
        missed = set()
        for attempt in attempts:
            for feedback in attempt.result["feedback"]:
                (missed.discard if feedback["correct"] else missed.add)(feedback["id"])
        bank.sort(key=lambda q: q["id"] not in missed)
    return save_quiz_session(module_id, bank[: 5 if module_id == 1 else 4], db)


def save_quiz_session(module_id, chosen, db):
    session = QuizSession(id=str(uuid4()), module_id=module_id, questions=chosen)
    db.add(session)
    db.commit()
    return {
        "session_id": session.id,
        "module_id": module_id,
        "questions": [
            {k: v for k, v in q.items() if k not in {"correct", "explanation"}}
            for q in chosen
        ],
    }


class QuizSubmission(BaseModel):
    session_id: UUID
    submission_id: UUID
    answers: dict[str, Annotated[int, Field(ge=0, le=20, strict=True)]]


@router.post("/modules/{module_id}/quiz")
def grade_quiz(module_id: int, request: QuizSubmission, db: DB):
    require_module(module_id)
    existing = db.scalar(
        select(QuizAttempt).where(
            QuizAttempt.submission_id == str(request.submission_id)
        )
    )
    if existing:
        if (
            existing.module_id != module_id
            or existing.session_id != str(request.session_id)
            or existing.answers != request.answers
        ):
            raise HTTPException(
                409, "Submission identifier was already used with different answers."
            )
        return existing.result
    session = db.get(QuizSession, str(request.session_id))
    if session is None or session.module_id != module_id:
        raise HTTPException(404, "Quiz session not found. Start a new quiz.")
    created = (
        session.created_at.replace(tzinfo=UTC)
        if session.created_at.tzinfo is None
        else session.created_at
    )
    if (datetime.now(UTC) - created).total_seconds() > 86400:
        raise HTTPException(410, "Quiz session expired. Start a new quiz.")
    if set(request.answers) != {q["id"] for q in session.questions}:
        raise HTTPException(
            422,
            "Answer every question exactly once; unknown questions are not accepted.",
        )
    if any(request.answers[q["id"]] >= len(q["options"]) for q in session.questions):
        raise HTTPException(422, "Answer option is outside the available choices.")
    feedback = [
        {
            "id": q["id"],
            "correct": request.answers[q["id"]] == q["correct"],
            "correct_answer": q["options"][q["correct"]],
            "explanation": q["explanation"],
            "topic": q["topic"],
        }
        for q in session.questions
    ]
    result = {
        "score": sum(q["correct"] for q in feedback),
        "total": len(feedback),
        "feedback": feedback,
    }
    db.add(
        QuizAttempt(
            submission_id=str(request.submission_id),
            session_id=session.id,
            module_id=module_id,
            score=result["score"],
            total=result["total"],
            answers=request.answers,
            result=result,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(QuizAttempt).where(
                QuizAttempt.submission_id == str(request.submission_id)
            )
        )
        if (
            existing
            and existing.answers == request.answers
            and existing.module_id == module_id
            and existing.session_id == session.id
        ):
            return existing.result
        raise HTTPException(409, "Conflicting submission identifier.")
    return result


@router.get("/modules/{module_id}/quiz-history")
def quiz_history(module_id: int, db: DB):
    require_module(module_id)
    attempts = db.scalars(
        select(QuizAttempt)
        .where(QuizAttempt.module_id == module_id)
        .order_by(QuizAttempt.id.desc())
        .limit(20)
    ).all()
    return [
        {
            "id": a.id,
            "score": a.score,
            "total": a.total,
            "created_at": a.created_at.isoformat(),
            "missed_topics": sorted(
                {f["topic"] for f in a.result["feedback"] if not f["correct"]}
            ),
        }
        for a in attempts
    ]


@router.get("/modules/{module_id}/scenarios")
def scenarios(module_id: int, challenge: bool = False):
    require_module(module_id)
    if module_id == 9:
        return e2e_case(challenge)
    if module_id == 10:
        d = 150 if challenge else 100
        return {
            "deadline_ms": d,
            "cases": [
                {
                    "label": "Fresh response",
                    "ready": True,
                    "command_sent": True,
                    "observations": [{"time_ms": d - 20, "state": "ACTIVE"}],
                },
                {
                    "label": "Boundary response",
                    "ready": True,
                    "command_sent": True,
                    "observations": [{"time_ms": d, "state": "ACTIVE"}],
                },
                {
                    "label": "Late response",
                    "ready": True,
                    "command_sent": True,
                    "observations": [{"time_ms": d + 20, "state": "ACTIVE"}],
                },
                {
                    "label": "No response",
                    "ready": True,
                    "command_sent": True,
                    "observations": [],
                },
                {
                    "label": "Invalid setup",
                    "ready": False,
                    "command_sent": True,
                    "observations": [],
                },
            ],
        }
    if module_id == 11:
        return {"cases": adas_cases(challenge)}
    raise HTTPException(404, "This module uses CAPL or signal configuration instead.")


@router.post("/tools/decode")
def decode_signal(request: DecodeRequest):
    try:
        return decode(request.data, request.settings)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/tools/e2e")
def e2e_tool(request: E2ERequest):
    return check_e2e(request)


@router.post("/tools/verdict")
def verdict_tool(request: VerdictRequest):
    return check_verdict(request)


@router.post("/tools/adas")
def adas_tool(request: ADASRequest):
    return adas_result(request)
