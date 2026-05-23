from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from typing import Any


class HashEmbeddingFunction:
    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(document) for document in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)

    @staticmethod
    def name() -> str:
        return "local_hash_embedding"

    def get_config(self) -> dict[str, Any]:
        return {"dimensions": 128}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "HashEmbeddingFunction":
        return HashEmbeddingFunction()

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        return

    def _embed(self, text: str, dimensions: int = 128) -> list[float]:
        vector = [0.0] * dimensions
        for token in text:
            if token.isspace():
                continue
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % dimensions
            vector[index] += 1.0
        length = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / length for value in vector]


class ChromaMemoryStore:
    def __init__(self, persist_path: str | None = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "data" / "chroma"
        self.persist_path = Path(persist_path or os.getenv("CHROMA_PATH", default_path))
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None
        self.available = False
        self.error = ""
        self._init_chroma()

    def upsert_npc_memories(self, case_id: str, npc_id: str, memories: list[tuple[str, str]]) -> None:
        self._ensure_available()
        ids = [f"{case_id}:{npc_id}:{kind}" for kind, content in memories if content.strip()]
        if ids:
            self._collection.delete(ids=ids)
        documents = [content for _, content in memories if content.strip()]
        if not documents:
            return
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=[{"case_id": case_id, "npc_id": npc_id, "kind": kind} for kind, content in memories if content.strip()],
        )

    def search_npc_memories(self, case_id: str, npc_id: str, query: str, limit: int = 4) -> list[str]:
        self._ensure_available()
        result = self._collection.query(
            query_texts=[query],
            n_results=limit,
            where={"$and": [{"case_id": {"$eq": case_id}}, {"npc_id": {"$eq": npc_id}}]},
        )
        documents = result.get("documents") or [[]]
        return list(documents[0])

    def delete_case(self, case_id: str) -> None:
        self._ensure_available()
        self._collection.delete(where={"case_id": {"$eq": case_id}})

    def delete_case_if_available(self, case_id: str) -> None:
        if self.available:
            self._collection.delete(where={"case_id": {"$eq": case_id}})

    def _init_chroma(self) -> None:
        try:
            import chromadb
        except ImportError as exc:
            self.error = "需要安装 chromadb：pip install chromadb"
            return

        self._client = chromadb.PersistentClient(path=str(self.persist_path))
        self._collection = self._client.get_or_create_collection(
            name="npc_private_memories",
            embedding_function=HashEmbeddingFunction(),
        )
        self.available = True

    def _ensure_available(self) -> None:
        if not self.available:
            raise RuntimeError(self.error or "Chroma memory store is not available")


class GameStorage:
    def __init__(self, db_path: str | None = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "data" / "game.db"
        self.db_path = Path(db_path or os.getenv("GAME_DB_PATH", default_path))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory = ChromaMemoryStore()
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

    def delete_case(self, case_id: str) -> None:
        self._execute("delete from case_scripts where case_id = ?", (case_id,))
        self._execute("delete from sessions where case_id = ?", (case_id,))
        self.memory.delete_case_if_available(case_id)

    def delete_client_case(self, client_id: str, case_id: str) -> None:
        self._execute("delete from sessions where client_id = ? and case_id = ?", (client_id, case_id))

    def save_session(self, session_id: str, case_id: str, client_id: str, payload: dict[str, Any]) -> None:
        self._execute(
            """
            insert into sessions(session_id, case_id, client_id, payload, updated_at)
            values (?, ?, ?, ?, ?)
            on conflict(session_id) do update set case_id = excluded.case_id, client_id = excluded.client_id, payload = excluded.payload, updated_at = excluded.updated_at
            """,
            (session_id, case_id, client_id, json.dumps(payload, ensure_ascii=False), self._now()),
        )

    def load_sessions(self) -> dict[str, dict[str, Any]]:
        rows = self._query("select session_id, client_id, payload from sessions")
        payloads = {}
        for row in rows:
            payload = json.loads(row["payload"])
            payload["client_id"] = payload.get("client_id") or row["client_id"] or "global"
            payloads[row["session_id"]] = payload
        return payloads

    def upsert_npc_memories(self, case_id: str, npc_id: str, memories: list[tuple[str, str]]) -> None:
        self.memory.upsert_npc_memories(case_id, npc_id, memories)

    def search_npc_memories(self, case_id: str, npc_id: str, query: str, limit: int = 4) -> list[str]:
        return self.memory.search_npc_memories(case_id, npc_id, query, limit)

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
                    client_id text not null default 'global',
                    payload text not null,
                    updated_at text not null
                );
                """
            )
            columns = {row["name"] for row in conn.execute("pragma table_info(sessions)")}
            if "client_id" not in columns:
                conn.execute("alter table sessions add column client_id text not null default 'global'")

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

    def _now(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds")
