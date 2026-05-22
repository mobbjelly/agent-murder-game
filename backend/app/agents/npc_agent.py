from __future__ import annotations

from collections.abc import Iterator

from app.agents.qwen import QwenClient
from app.game.models import Clue, NPCState
from app.game.storage import GameStorage


class NPCAgent:
    def __init__(self, case_id: str, npc_id: str, state: NPCState, storage: GameStorage, qwen: QwenClient) -> None:
        self.case_id = case_id
        self.npc_id = npc_id
        self.state = state
        self.storage = storage
        self.qwen = qwen

    def reply(self, player_input: str, shared_context: str, confronted_clue: Clue | None = None) -> str:
        return self.qwen.chat(self._messages(player_input, shared_context, confronted_clue))

    def stream_reply(self, player_input: str, shared_context: str, confronted_clue: Clue | None = None) -> Iterator[str]:
        yield from self.qwen.stream_chat(self._messages(player_input, shared_context, confronted_clue))

    def _messages(self, player_input: str, shared_context: str, confronted_clue: Clue | None) -> list[dict[str, str]]:
        private_memories = self.storage.search_npc_memories(self.case_id, self.npc_id, player_input)
        memory_context = "\n".join(private_memories) if private_memories else "未检索到额外私有记忆。"
        clue_line = f"正在被对质的证据：{confronted_clue.name} - {confronted_clue.description}" if confronted_clue else ""
        return [
            {
                "role": "system",
                "content": (
                    f"你是一个独立 NPC Agent：{self.state.name}（{self.state.title}）。"
                    "你只能使用自己的私有记忆、当前公开案情和玩家刚才的话回答。"
                    "不要泄露其他 NPC 的秘密；不知道就回避、试探或要求证据。"
                    "根据关系值决定是否防备、撒谎、松口。回答控制在 120 字内。\n"
                    f"你的私有长期记忆：{memory_context}\n"
                    f"当前关系值：信任 {self.state.relation.trust}，警惕 {self.state.relation.fear}，压力 {self.state.relation.pressure}。\n"
                    f"共享短期记忆/公开案情：{shared_context}\n{clue_line}"
                ),
            },
            {"role": "user", "content": player_input},
        ]
