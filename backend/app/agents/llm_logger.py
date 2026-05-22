from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import time
from typing import Any


class LLMCallLogger:
    def __init__(self, log_path: str | None = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "data" / "logs" / "llm_calls.jsonl"
        self.log_path = Path(log_path or os.getenv("LLM_LOG_PATH", default_path))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def start(self) -> float:
        return time.perf_counter()

    def write(
        self,
        *,
        provider: str,
        model: str,
        operation: str,
        started_at: float,
        status: str,
        prompt_preview: str = "",
        response_preview: str = "",
        error: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "provider": provider,
            "model": model,
            "operation": operation,
            "status": status,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "prompt_preview": self._preview(prompt_preview),
            "response_preview": self._preview(response_preview),
            "error": self._preview(error, 500),
            "metadata": metadata or {},
        }
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def prompt_from_messages(self, messages: list[dict[str, str]]) -> str:
        return "\n".join(f"{item.get('role', '')}: {item.get('content', '')}" for item in messages)

    def _preview(self, value: str, limit: int = 800) -> str:
        value = value or ""
        return value if len(value) <= limit else value[:limit] + "..."
