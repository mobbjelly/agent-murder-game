from __future__ import annotations

import os
from typing import Any


class DeepDMAgent:
    """可选的 DeepAgents 主持人层。"""

    def __init__(self) -> None:
        self._agent: Any | None = None
        self._ready = False
        self._init_agent()

    @property
    def ready(self) -> bool:
        return self._ready

    def summarize_scene(self, context: str) -> str:
        if not self._agent:
            return "DM：案情看板已更新。继续质询嫌疑人，或去新的地点搜证。"
        try:
            result = self._agent.invoke({"messages": [{"role": "user", "content": context}]})
            messages = result.get("messages", []) if isinstance(result, dict) else []
            if messages:
                last = messages[-1]
                return getattr(last, "content", str(last)).strip()
        except Exception:
            pass
        return "DM：新的信息改变了嫌疑人的心理防线，试着用证据对质。"

    def _init_agent(self) -> None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return
        try:
            from deepagents import create_deep_agent
            from langchain_openai import ChatOpenAI

            model = ChatOpenAI(
                api_key=api_key,
                base_url=os.getenv(
                    "DASHSCOPE_BASE_URL",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                ),
                model=os.getenv("QWEN_MODEL", "qwen-plus"),
                temperature=0.6,
            )
            self._agent = create_deep_agent(
                model=model,
                tools=[],
                system_prompt=(
                    "你是 AI 剧本杀主持人 DM。根据案情变化，用 1-2 句中文给玩家下一步引导。"
                    "不要泄露真凶，只提示可调查方向。"
                ),
            )
            self._ready = True
        except Exception:
            self._agent = None
            self._ready = False
