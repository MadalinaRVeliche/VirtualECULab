import re
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.can_frames import StandardCanFrame
from backend.capl_can import simulate_can_program
from backend.database import get_db
from backend.learning_api import router as learning_router
from backend.models import LessonProgress

app = FastAPI(title="Virtual ECU Lab")

# The learning router owns the Workbench endpoint (/lab/run), course
# metadata, and quizzes. This file also keeps the original lesson routes.
app.include_router(learning_router)

# In development, Vite and FastAPI run on different origins.
# The hosted build serves both from the same origin through backend/web.py.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    # Render uses this endpoint to check that the web process responds.
    return {"status": "ok"}


@app.get("/lessons")
def get_lessons():
    return [
        {
            "id": 1,
            "title": "Your first CAPL event",
            "description": (
                "The on start event runs when the simulation starts. "
                "The write function displays a message in the simulator console."
            ),
            "task": (
                "Write an on start event that prints exactly one message: ECU ready"
            ),
            "code": 'on start\n{\n  write("Hello, ECU!");\n}',
        },
        {
            "id": 2,
            "title": "Multiple messages",
            "description": (
                "Statements inside on start run in order. "
                "Each write statement displays a separate message."
            ),
            "task": (
                "Print exactly two messages in this order: "
                "Starting ECU, then System ready."
            ),
            "code": (
                'on start\n{\n  write("First message");\n  write("Second message");\n}'
            ),
        },
        {
            "id": 3,
            "title": "Keyboard events",
            "description": (
                "An on key event runs when its matching key is pressed. "
                "Starting the simulation does not trigger this event."
            ),
            "task": (
                "Write an on key 'a' event that prints exactly one message: "
                "Key A pressed"
            ),
            "code": ("on key 'a'\n{\n  write(\"Your message\");\n}"),
        },
    ]


class SimulationRequest(BaseModel):
    code: str
    event: Literal["start", "key"] = "start"
    key: str | None = Field(default=None, min_length=1, max_length=1)


@app.post("/simulate")
def simulate(request: SimulationRequest):
    if request.event == "key" and request.key is None:
        raise HTTPException(
            status_code=400,
            detail="A key event requires a single key character.",
        )

    # Programs with a variables block use the single-message CAN parser.
    # The introductory lessons below use a handler containing only write().
    if re.match(r"\s*variables\b", request.code):
        try:
            return simulate_can_program(
                request.code,
                event=request.event,
                key=request.key,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

    event_match = re.fullmatch(
        r"\s*on\s+(start|key\s+'([^'\\\r\n])')\s*\{(.*)\}\s*",
        request.code,
        flags=re.DOTALL,
    )

    if event_match is None:
        raise HTTPException(
            status_code=400,
            detail=("Code must contain a single on start or on key 'character' event."),
        )

    declared_event = "start" if event_match.group(1) == "start" else "key"
    declared_key = event_match.group(2)
    body = event_match.group(3)

    instruction_pattern = re.compile(r'\s*write\s*\(\s*"([^"\\\r\n]*)"\s*\)\s*;')

    output = []
    position = 0

    # Read consecutive statements from the current position. Searching
    # for write() calls anywhere in the body could skip invalid code.
    while position < len(body):
        if not body[position:].strip():
            break

        instruction = instruction_pattern.match(body, position)

        if instruction is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    'Only write("message"); statements are supported. '
                    "Escape sequences are not supported."
                ),
            )

        output.append(instruction.group(1))
        position = instruction.end()

    # Validate the handler body first. Its output is visible only when
    # the requested event and, for key events, the character match.
    should_execute = declared_event == request.event and (
        declared_event == "start" or declared_key == request.key
    )

    return {"output": output if should_execute else []}


class ExerciseSubmission(BaseModel):
    code: str


@app.post("/lessons/{lesson_id}/check")
def check_exercise(
    lesson_id: int,
    submission: ExerciseSubmission,
    db: Annotated[Session, Depends(get_db)],
):
    expected_outputs = {
        1: ["ECU ready"],
        2: ["Starting ECU", "System ready"],
        3: ["Key A pressed"],
    }

    if lesson_id not in expected_outputs:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found.",
        )

    # Grade with the same simulator used by /simulate. The keyboard
    # exercise supplies 'a' as its stimulus; the other two use startup.
    result = simulate(
        SimulationRequest(
            code=submission.code,
            event="key" if lesson_id == 3 else "start",
            key="a" if lesson_id == 3 else None,
        )
    )
    expected_output = expected_outputs[lesson_id]

    # List equality checks the message text, count, and order together.
    passed = result["output"] == expected_output

    if passed:
        # A repeat pass keeps the existing completion record.
        progress = db.get(LessonProgress, lesson_id)

        if progress is None:
            db.add(LessonProgress(lesson_id=lesson_id))
            db.commit()

    expected_text = " → ".join(expected_output)

    return {
        "passed": passed,
        "output": result["output"],
        "message": (
            "Correct! You completed the exercise."
            if passed
            else f"Expected messages in this exact order: {expected_text}"
        ),
    }


@app.get("/progress")
def get_progress(db: Annotated[Session, Depends(get_db)]):
    completed_ids = db.scalars(
        select(LessonProgress.lesson_id).order_by(LessonProgress.lesson_id)
    ).all()

    return {"completed_lesson_ids": completed_ids}


@app.post("/can/frames/preview")
def preview_can_frame(frame: StandardCanFrame):
    # FastAPI validates the frame before the handler formats it for display.
    return frame.preview()