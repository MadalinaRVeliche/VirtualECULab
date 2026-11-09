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
            "title": "Primul eveniment CAPL",
            "description": (
                "Evenimentul on start se execută la pornirea simulării. "
                "Funcția write afișează un mesaj în consola simulatorului."
            ),
            "code": 'on start\n{\n  write("Salut, ECU!");\n}',
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
            detail="Codul trebuie să conțină un singur eveniment on start.",
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
                    "În on start sunt acceptate doar instrucțiuni "
                    'write("mesaj");, fără secvențe de escape.'
                ),
            )

        output.append(instruction.group(1))
        position = instruction.end()

    return {"output": output}
