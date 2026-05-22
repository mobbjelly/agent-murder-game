from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

from app.agents.llm_logger import LLMCallLogger


class QwenImageClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.model = os.getenv("QWEN_IMAGE_MODEL", "qwen-image-2.0")
        base_url = os.getenv("DASHSCOPE_IMAGE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        self.endpoint = f"{base_url.rstrip('/')}/services/aigc/multimodal-generation/generation"
        self.size = os.getenv("QWEN_IMAGE_SIZE", "1328*1328")
        self.assets_dir = Path(os.getenv("GENERATED_ASSETS_DIR", Path(__file__).resolve().parents[2] / "data" / "generated"))
        self.assets_url_prefix = os.getenv("GENERATED_ASSETS_URL_PREFIX", "/assets/generated")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.last_error = ""
        self.logger = LLMCallLogger()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, fallback_url: str) -> str:
        started_at = self.logger.start()
        if not self.enabled:
            self.last_error = "DASHSCOPE_API_KEY is not configured"
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="image_generate",
                started_at=started_at,
                status="disabled",
                prompt_preview=prompt,
                response_preview=fallback_url,
                error=self.last_error,
                metadata={"size": self.size},
            )
            return fallback_url
        try:
            image_url = self._request_image(prompt)
            self.last_error = ""
            local_url = self._download_image(image_url)
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="image_generate",
                started_at=started_at,
                status="ok",
                prompt_preview=prompt,
                response_preview=local_url,
                metadata={"size": self.size, "remote_url": image_url},
            )
            return local_url
        except Exception as exc:
            self.last_error = f"{exc.__class__.__name__}: {exc}"
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="image_generate",
                started_at=started_at,
                status="fallback",
                prompt_preview=prompt,
                response_preview=fallback_url,
                error=self.last_error,
                metadata={"size": self.size},
            )
            return fallback_url

    def _request_image(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "negative_prompt": "low quality, blurry, distorted face, extra fingers, watermark, text artifacts, oversaturated",
                "prompt_extend": True,
                "watermark": False,
                "size": self.size,
                "n": 1,
            },
        }
        request = Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["output"]["choices"][0]["message"]["content"]
        for item in content:
            if item.get("image"):
                return item["image"]
        raise ValueError("Qwen-Image response did not include an image URL")

    def _download_image(self, image_url: str) -> str:
        suffix = ".png"
        filename = f"{uuid4().hex}{suffix}"
        filepath = self.assets_dir / filename
        with urlopen(image_url, timeout=120) as response:
            filepath.write_bytes(response.read())
        return f"{self.assets_url_prefix}/{filename}"
