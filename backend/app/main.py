from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.game.engine import GameEngine
from app.game.models import AccuseRequest, ConfrontRequest, NewGameRequest, PlayerMessage, SearchRequest


load_dotenv()

app = FastAPI(title="AI Murder Mystery", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = GameEngine()


@app.get("/api/health")
def health() -> dict[str, bool | str]:
    return {
        "ok": True,
        "qwen_enabled": engine.qwen.enabled,
        "deepagents_enabled": engine.dm.ready,
        "database": str(engine.storage.db_path),
    }


@app.post("/api/game/new")
def new_game(request: NewGameRequest | None = None):
    try:
        return engine.new_game(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/cases")
def list_cases():
    return engine.list_cases()


@app.get("/api/game/{session_id}")
def get_game(session_id: str):
    try:
        return engine.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/talk")
def talk(session_id: str, request: PlayerMessage):
    try:
        return engine.talk(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/search")
def search(session_id: str, request: SearchRequest):
    try:
        return engine.search(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/confront")
def confront(session_id: str, request: ConfrontRequest):
    try:
        return engine.confront(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/accuse")
def accuse(session_id: str, request: AccuseRequest):
    try:
        return engine.accuse(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
