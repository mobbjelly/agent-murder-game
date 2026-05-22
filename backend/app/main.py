from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import json

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
app.mount("/assets/generated", StaticFiles(directory=engine.image.assets_dir), name="generated-assets")


@app.get("/api/health")
def health() -> dict[str, bool | str]:
    return {
        "ok": True,
        "qwen_enabled": engine.qwen.enabled,
        "qwen_image_enabled": engine.image.enabled,
        "qwen_image_model": engine.image.model,
        "qwen_image_last_error": engine.image.last_error,
        "llm_log_path": str(engine.qwen.logger.log_path),
        "deepagents_enabled": engine.dm.ready,
        "chroma_enabled": engine.storage.memory.available,
        "database": str(engine.storage.db_path),
    }


@app.post("/api/game/new")
def new_game(request: NewGameRequest | None = None):
    try:
        return engine.new_game(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/cases")
def list_cases():
    return engine.list_cases()


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str):
    try:
        return engine.delete_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/game/{session_id}")
def get_game(session_id: str):
    try:
        return engine.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/talk")
def talk(session_id: str, request: PlayerMessage):
    try:
        return engine.talk(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/talk/stream")
def stream_talk(session_id: str, request: PlayerMessage):
    def events():
        try:
            for event in engine.stream_talk(session_id, request):
                payload = event.copy()
                if payload.get("game") is not None:
                    payload["game"] = payload["game"].model_dump()
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except KeyError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"
        except RuntimeError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


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
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/accuse")
def accuse(session_id: str, request: AccuseRequest):
    try:
        return engine.accuse(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
