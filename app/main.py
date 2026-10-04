from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .quantum import DEFAULT_QUBITS, MAX_QUBITS, ask

app = FastAPI(title="Quantum Magic 8-Ball")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class AskRequest(BaseModel):
    question: str = Field(default="", max_length=280)
    qubits: int = Field(default=DEFAULT_QUBITS, ge=1, le=MAX_QUBITS)


@app.post("/api/ask")
def ask_endpoint(req: AskRequest):
    try:
        return ask(req.question, req.qubits)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
