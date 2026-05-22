from __future__ import annotations

import os
from http import HTTPStatus
from collections.abc import Iterator

from app.agents.llm_logger import LLMCallLogger


class QwenClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.model = os.getenv("QWEN_MODEL", "qwen-plus")
        self.logger = LLMCallLogger()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        started_at = self.logger.start()
        prompt_preview = self.logger.prompt_from_messages(messages)
        if not self.enabled:
            response = self._mock_response(messages)
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="chat",
                started_at=started_at,
                status="mock",
                prompt_preview=prompt_preview,
                response_preview=response,
                metadata={"temperature": temperature},
            )
            return response

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
                content = response.output.choices[0].message.content.strip()
                self.logger.write(
                    provider="dashscope",
                    model=self.model,
                    operation="chat",
                    started_at=started_at,
                    status="ok",
                    prompt_preview=prompt_preview,
                    response_preview=content,
                    metadata={"temperature": temperature},
                )
                return content
            error = f"通义千问调用失败：{response.code} - {response.message}"
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="chat",
                started_at=started_at,
                status="error",
                prompt_preview=prompt_preview,
                error=error,
                metadata={"temperature": temperature},
            )
            return error
        except Exception as exc:
            response = f"本地降级回复：模型暂不可用（{exc.__class__.__name__}）。{self._mock_response(messages)}"
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="chat",
                started_at=started_at,
                status="fallback",
                prompt_preview=prompt_preview,
                response_preview=response,
                error=f"{exc.__class__.__name__}: {exc}",
                metadata={"temperature": temperature},
            )
            return response

    def stream_chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> Iterator[str]:
        started_at = self.logger.start()
        prompt_preview = self.logger.prompt_from_messages(messages)
        if not self.enabled:
            response = self._mock_response(messages)
            yield from self._stream_text(response)
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="stream_chat",
                started_at=started_at,
                status="mock",
                prompt_preview=prompt_preview,
                response_preview=response,
                metadata={"temperature": temperature},
            )
            return

        try:
            from dashscope import Generation

            responses = Generation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                result_format="message",
                temperature=temperature,
                stream=True,
                incremental_output=True,
            )
            chunks: list[str] = []
            for response in responses:
                if response.status_code == HTTPStatus.OK:
                    content = response.output.choices[0].message.content
                    if content:
                        chunks.append(content)
                        yield content
                else:
                    error = f"通义千问调用失败：{response.code} - {response.message}"
                    yield error
                    self.logger.write(
                        provider="dashscope",
                        model=self.model,
                        operation="stream_chat",
                        started_at=started_at,
                        status="error",
                        prompt_preview=prompt_preview,
                        response_preview="".join(chunks),
                        error=error,
                        metadata={"temperature": temperature},
                    )
                    return
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="stream_chat",
                started_at=started_at,
                status="ok",
                prompt_preview=prompt_preview,
                response_preview="".join(chunks),
                metadata={"temperature": temperature, "chunks": len(chunks)},
            )
        except Exception as exc:
            response = f"本地降级回复：模型暂不可用（{exc.__class__.__name__}）。{self._mock_response(messages)}"
            yield from self._stream_text(response)
            self.logger.write(
                provider="dashscope",
                model=self.model,
                operation="stream_chat",
                started_at=started_at,
                status="fallback",
                prompt_preview=prompt_preview,
                response_preview=response,
                error=f"{exc.__class__.__name__}: {exc}",
                metadata={"temperature": temperature},
            )

    def _stream_text(self, text: str) -> Iterator[str]:
        for char in text:
            yield char

    def _mock_response(self, messages: list[dict[str, str]]) -> str:
        user_text = messages[-1]["content"] if messages else ""
        if "证据" in user_text or "解释" in user_text:
            return "我承认这件事看起来可疑，但它并不能证明我杀了人。你还缺少动机和完整时间线。"
        if "遗嘱" in user_text:
            return "遗嘱？我只是听说老爷最近心情不好，具体内容我并不清楚。"
        return "那晚每个人都很紧张。我只能告诉你，我没有杀人，但有些事我需要确认你是否已经知道。"
