import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Virtual ECU Lab")

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
        }
    ]


class SimulationRequest(BaseModel):
    code: str


@app.post("/simulate")
def simulate(request: SimulationRequest):
    event_match = re.fullmatch(
        r"\s*on\s+start\s*\{(.*)\}\s*",
        request.code,
        flags=re.DOTALL,
    )

    if event_match is None:
        raise HTTPException(
            status_code=400,
            detail="Code must contain a single on start event.",
        )

    body = event_match.group(1)
    instruction_pattern = re.compile(r'\s*write\s*\(\s*"([^"\\\r\n]*)"\s*\)\s*;')

    output = []
    position = 0

    while position < len(body):
        if not body[position:].strip():
            break

        instruction = instruction_pattern.match(body, position)

        if instruction is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    'Only write("message"); statements are supported '
                    "inside on start. Escape sequences are not supported."
                ),
            )

        output.append(instruction.group(1))
        position = instruction.end()

    return {"output": output}


class ExerciseSubmission(BaseModel):
    code: str


@app.post("/lessons/{lesson_id}/check")
def check_exercise(lesson_id: int, submission: ExerciseSubmission):
    if lesson_id != 1:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found.",
        )

    result = simulate(SimulationRequest(code=submission.code))
    expected_output = ["ECU ready"]
    passed = result["output"] == expected_output

    return {
        "passed": passed,
        "output": result["output"],
        "message": (
            "Correct! You completed the exercise."
            if passed
            else "Expected exactly one message: ECU ready"
        ),
    }
