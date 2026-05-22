from __future__ import annotations

import os
from http import HTTPStatus


class QwenClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.model = os.getenv("QWEN_MODEL", "qwen-plus")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        if not self.enabled:
            return self._mock_response(messages)

        try:
            from dashscope import Generation

            response = Generation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                result_format="message",
                temperature=temperature,
            )
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content.strip()
            return f"通义千问调用失败：{response.code} - {response.message}"
        except Exception as exc:
            return f"本地降级回复：模型暂不可用（{exc.__class__.__name__}）。{self._mock_response(messages)}"

    def _mock_response(self, messages: list[dict[str, str]]) -> str:
        user_text = messages[-1]["content"] if messages else ""
        if "证据" in user_text or "解释" in user_text:
            return "我承认这件事看起来可疑，但它并不能证明我杀了人。你还缺少动机和完整时间线。"
        if "遗嘱" in user_text:
            return "遗嘱？我只是听说老爷最近心情不好，具体内容我并不清楚。"
        return "那晚每个人都很紧张。我只能告诉你，我没有杀人，但有些事我需要确认你是否已经知道。"

