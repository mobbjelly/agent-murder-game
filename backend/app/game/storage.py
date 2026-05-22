from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from typing import Any


class GameStorage:
    def __init__(self, db_path: str | None = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "data" / "game.db"
        self.db_path = Path(db_path or os.getenv("GAME_DB_PATH", default_path))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def save_case_script(self, case_id: str, payload: dict[str, Any]) -> None:
        self._execute(
            """
            insert into case_scripts(case_id, payload, updated_at)
            values (?, ?, ?)
            on conflict(case_id) do update set payload = excluded.payload, updated_at = excluded.updated_at
            """,
            (case_id, json.dumps(payload, ensure_ascii=False), self._now()),
        )

    def load_case_scripts(self) -> dict[str, dict[str, Any]]:
        rows = self._query("select case_id, payload from case_scripts")
        return {row["case_id"]: json.loads(row["payload"]) for row in rows}

    def save_session(self, session_id: str, case_id: str, payload: dict[str, Any]) -> None:
        self._execute(
            """
            insert into sessions(session_id, case_id, payload, updated_at)
            values (?, ?, ?, ?)
            on conflict(session_id) do update set case_id = excluded.case_id, payload = excluded.payload, updated_at = excluded.updated_at
            """,
            (session_id, case_id, json.dumps(payload, ensure_ascii=False), self._now()),
        )

    def load_sessions(self) -> dict[str, dict[str, Any]]:
        rows = self._query("select session_id, payload from sessions")
        return {row["session_id"]: json.loads(row["payload"]) for row in rows}

    def upsert_npc_memories(self, case_id: str, npc_id: str, memories: list[tuple[str, str]]) -> None:
        self._execute("delete from npc_memories where case_id = ? and npc_id = ?", (case_id, npc_id))
        with self._connect() as conn:
            conn.executemany(
                """
                insert into npc_memories(case_id, npc_id, kind, content, embedding, updated_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        case_id,
                        npc_id,
                        kind,
                        content,
                        json.dumps(self._embed(content)),
                        self._now(),
                    )
                    for kind, content in memories
                    if content.strip()
                ],
            )

    def search_npc_memories(self, case_id: str, npc_id: str, query: str, limit: int = 4) -> list[str]:
        rows = self._query(
            "select content, embedding from npc_memories where case_id = ? and npc_id = ?",
            (case_id, npc_id),
        )
        if not rows:
            return []
        query_embedding = self._embed(query)
        scored = []
        for row in rows:
            embedding = json.loads(row["embedding"])
            scored.append((self._cosine(query_embedding, embedding), row["content"]))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [content for _, content in scored[:limit]]

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists case_scripts(
                    case_id text primary key,
                    payload text not null,
                    updated_at text not null
                );
                create table if not exists sessions(
                    session_id text primary key,
                    case_id text not null,
                    payload text not null,
                    updated_at text not null
                );
                create table if not exists npc_memories(
                    id integer primary key autoincrement,
                    case_id text not null,
                    npc_id text not null,
                    kind text not null,
                    content text not null,
                    embedding text not null,
                    updated_at text not null
                );
                create index if not exists idx_npc_memories_lookup on npc_memories(case_id, npc_id);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._connect() as conn:
            conn.execute(sql, params)

    def _query(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params))

    def _embed(self, text: str, dimensions: int = 64) -> list[float]:
        vector = [0.0] * dimensions
        tokens = [char for char in text if not char.isspace()]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % dimensions
            vector[index] += 1.0
        length = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / length for value in vector]

    def _cosine(self, left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right))

    def _now(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds")
