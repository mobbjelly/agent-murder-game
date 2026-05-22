from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4


class QwenImageClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.model = os.getenv("QWEN_IMAGE_MODEL", "qwen-image-2.0-pro")
        base_url = os.getenv("DASHSCOPE_IMAGE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        self.endpoint = f"{base_url.rstrip('/')}/services/aigc/multimodal-generation/generation"
        self.size = os.getenv("QWEN_IMAGE_SIZE", "1328*1328")
        self.assets_dir = Path(os.getenv("GENERATED_ASSETS_DIR", Path(__file__).resolve().parents[2] / "data" / "generated"))
        self.assets_url_prefix = os.getenv("GENERATED_ASSETS_URL_PREFIX", "/assets/generated")
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, fallback_url: str) -> str:
        if not self.enabled:
            return fallback_url
        try:
            image_url = self._request_image(prompt)
            return self._download_image(image_url)
        except Exception:
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
