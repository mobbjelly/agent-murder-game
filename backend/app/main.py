from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import json

from app.game.engine import GameEngine
from app.game.models import AccuseRequest, ConfrontRequest, GenerateCaseRequest, NewGameRequest, PlayerMessage, SearchRequest


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
def list_cases(x_client_id: str = Header(default="global")):
    return engine.list_cases(x_client_id)


@app.post("/api/admin/cases/generate")
def generate_case(request: GenerateCaseRequest):
    try:
        return engine.generate_case(request.difficulty).summary
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/admin/cases")
def list_admin_cases():
    return engine.list_admin_cases()


@app.delete("/api/admin/cases/{case_id}")
def delete_admin_case(case_id: str):
    try:
        return engine.delete_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str, x_client_id: str = Header(default="global")):
    try:
        return engine.delete_client_case(x_client_id, case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/game/{session_id}")
def get_game(session_id: str, x_client_id: str = Header(default="global")):
    try:
        return engine.get(session_id, x_client_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/debug/game/{session_id}/npcs")
def debug_npcs(session_id: str, x_client_id: str = Header(default="")):
    try:
        return engine.debug_npcs(session_id, x_client_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/talk")
def talk(session_id: str, request: PlayerMessage, x_client_id: str = Header(default="global")):
    try:
        return engine.talk(session_id, request, x_client_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/talk/stream")
def stream_talk(session_id: str, request: PlayerMessage, x_client_id: str = Header(default="global")):
    def events():
        try:
            for event in engine.stream_talk(session_id, request, x_client_id):
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
def search(session_id: str, request: SearchRequest, x_client_id: str = Header(default="global")):
    try:
        return engine.search(session_id, request, x_client_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/confront")
def confront(session_id: str, request: ConfrontRequest, x_client_id: str = Header(default="global")):
    try:
        return engine.confront(session_id, request, x_client_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/game/{session_id}/accuse")
def accuse(session_id: str, request: AccuseRequest, x_client_id: str = Header(default="global")):
    try:
        return engine.accuse(session_id, request, x_client_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
