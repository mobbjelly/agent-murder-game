from __future__ import annotations

from copy import deepcopy
from collections.abc import Iterator
from datetime import datetime
import json
import re
from uuid import uuid4

from app.agents.deep_dm import DeepDMAgent
from app.agents.npc_agent import NPCAgent
from app.agents.qwen import QwenClient
from app.game.models import (
    AccuseRequest,
    ActionResponse,
    CaseSummary,
    ChatMessage,
    Clue,
    ConfrontRequest,
    Difficulty,
    GameView,
    NPCState,
    NewGameRequest,
    PlayerMessage,
    SearchRequest,
    SceneImage,
)
from app.game.media import svg_data
from app.game.storage import GameStorage


class CaseScript:
    def __init__(
        self,
        summary: CaseSummary,
        intro: str,
        locations: list[str],
        scene_images: list[SceneImage],
        npcs: dict[str, dict[str, NPCState | str]],
        clues: list[Clue],
        truth: dict[str, str],
    ) -> None:
        self.summary = summary
        self.intro = intro
        self.locations = locations
        self.scene_images = scene_images
        self.npcs = npcs
        self.clues = clues
        self.truth = truth

    def to_payload(self) -> dict:
        return {
            "summary": self.summary.model_dump(),
            "intro": self.intro,
            "locations": self.locations,
            "scene_images": [scene.model_dump() for scene in self.scene_images],
            "npcs": {
                npc_id: {
                    "state": data["state"].model_dump(),
                    "private_memory": data["private_memory"],
                }
                for npc_id, data in self.npcs.items()
            },
            "clues": [clue.model_dump() for clue in self.clues],
            "truth": self.truth,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "CaseScript":
        return cls(
            summary=CaseSummary(**payload["summary"]),
            intro=payload["intro"],
            locations=list(payload["locations"]),
            scene_images=[SceneImage(**item) for item in payload["scene_images"]],
            npcs={
                npc_id: {
                    "state": NPCState(**data["state"]),
                    "private_memory": data["private_memory"],
                }
                for npc_id, data in payload["npcs"].items()
            },
            clues=[Clue(**item) for item in payload["clues"]],
            truth=dict(payload["truth"]),
        )


def scene_fallback(title: str, subtitle: str) -> str:
    return svg_data(title, subtitle, "#3b332d", "#d0a35f")


class GameSession:
    def __init__(self, session_id: str, script: CaseScript, storage: GameStorage, qwen: QwenClient) -> None:
        self.session_id = session_id
        self.script = deepcopy(script)
        self.storage = storage
        self.qwen = qwen
        self.case = deepcopy(script.summary)
        self.phase = "intro"
        self.npcs: dict[str, NPCState] = {
            npc_id: deepcopy(data["state"]) for npc_id, data in self.script.npcs.items()
        }
        self.npc_agents = self._build_agents()
        self.clues: list[Clue] = deepcopy(self.script.clues)
        self.chat: list[ChatMessage] = [
            ChatMessage(speaker="DM", role="dm", content=self.script.intro),
            ChatMessage(
                speaker="DM",
                role="dm",
                content="你可以选择嫌疑人进行质询，点击案场图片搜证，或在证据足够后提交最终指控。",
            ),
        ]

    def to_payload(self) -> dict:
        return {
            "session_id": self.session_id,
            "case": self.case.model_dump(),
            "phase": self.phase,
            "npcs": {npc_id: npc.model_dump() for npc_id, npc in self.npcs.items()},
            "clues": [clue.model_dump() for clue in self.clues],
            "chat": [message.model_dump() for message in self.chat],
        }

    @classmethod
    def from_payload(cls, payload: dict, script: CaseScript, storage: GameStorage, qwen: QwenClient) -> "GameSession":
        session = cls(payload["session_id"], script, storage, qwen)
        session.case = CaseSummary(**payload["case"])
        session.phase = payload["phase"]
        session.npcs = {npc_id: NPCState(**data) for npc_id, data in payload["npcs"].items()}
        session.npc_agents = session._build_agents()
        session.clues = [Clue(**item) for item in payload["clues"]]
        session.chat = [ChatMessage(**item) for item in payload["chat"]]
        return session

    def agent(self, npc_id: str) -> NPCAgent:
        if npc_id not in self.npc_agents:
            raise KeyError("NPC 不存在。")
        return self.npc_agents[npc_id]

    def _build_agents(self) -> dict[str, NPCAgent]:
        return {
            npc_id: NPCAgent(self.case.id, npc_id, npc, self.storage, self.qwen)
            for npc_id, npc in self.npcs.items()
        }

    def view(self) -> GameView:
        return GameView(
            session_id=self.session_id,
            case=self.case,
            phase=self.phase,
            intro=self.script.intro,
            locations=self.script.locations,
            scene_images=self.script.scene_images,
            npcs=list(self.npcs.values()),
            discovered_clues=[clue for clue in self.clues if clue.discovered],
            chat=self.chat,
        )


class GameEngine:
    def __init__(self) -> None:
        self.sessions: dict[str, GameSession] = {}
        self.generated_cases: dict[str, CaseScript] = {}
        self.storage = GameStorage()
        self.qwen = QwenClient()
        self.dm = DeepDMAgent()
        self._restore()

    def list_cases(self) -> list[CaseSummary]:
        active_case_ids = {session.case.id for session in self.sessions.values()}
        cases = [deepcopy(script.summary) for script in self.generated_cases.values()]
        for case in cases:
            if case.id in active_case_ids:
                case.updated_label = "调查中"
        return cases

    def new_game(self, request: NewGameRequest | None = None) -> GameView:
        request = request or NewGameRequest()
        script = self._script(request.case_id, request.difficulty)
        script.summary.difficulty = request.difficulty
        script.summary.status = "unsolved"
        script.summary.updated_label = "未侦破"
        session_id = str(uuid4())
        self.sessions[session_id] = GameSession(session_id, script, self.storage, self.qwen)
        self._persist_script(script)
        self._persist_session(self.sessions[session_id])
        return self.sessions[session_id].view()

    def get(self, session_id: str) -> GameView:
        return self._session(session_id).view()

    def talk(self, session_id: str, request: PlayerMessage) -> ActionResponse:
        session = self._session(session_id)
        npc = self._npc(session, request.npc_id)
        session.phase = "investigate"
        session.chat.append(ChatMessage(speaker="你", role="player", content=request.message))

        self._adjust_relation(npc, request.message)
        answer = self._npc_reply(session, request.npc_id, request.message)
        session.chat.append(ChatMessage(speaker=npc.name, role="npc", content=answer))
        self._persist_session(session)
        return ActionResponse(game=session.view(), result=answer)

    def stream_talk(self, session_id: str, request: PlayerMessage) -> Iterator[dict[str, str | GameView]]:
        session = self._session(session_id)
        npc = self._npc(session, request.npc_id)
        session.phase = "investigate"
        session.chat.append(ChatMessage(speaker="你", role="player", content=request.message))
        self._adjust_relation(npc, request.message)
        answer_parts: list[str] = []
        yield {"type": "game", "game": session.view()}
        for chunk in session.agent(request.npc_id).stream_reply(request.message, self._shared_context(session)):
            answer_parts.append(chunk)
            yield {"type": "chunk", "content": chunk}
        answer = "".join(answer_parts)
        session.chat.append(ChatMessage(speaker=npc.name, role="npc", content=answer))
        self._persist_session(session)
        yield {"type": "game", "game": session.view()}

    def search(self, session_id: str, request: SearchRequest) -> ActionResponse:
        session = self._session(session_id)
        session.phase = "investigate"
        clue = next(
            (item for item in self.clues_for(session, request.location) if not item.discovered),
            None,
        )
        if clue is None:
            result = f"你仔细搜索了{request.location}，暂时没有发现新的线索。"
        else:
            clue.discovered = True
            result = f"你在{request.location}发现了【{clue.name}】：{clue.description}"
        session.chat.append(ChatMessage(speaker="DM", role="dm", content=result))

        dm_hint = self.dm.summarize_scene(self._shared_context(session))
        session.chat.append(ChatMessage(speaker="DM", role="dm", content=dm_hint))
        self._persist_session(session)
        return ActionResponse(game=session.view(), result=result)

    def confront(self, session_id: str, request: ConfrontRequest) -> ActionResponse:
        session = self._session(session_id)
        npc = self._npc(session, request.npc_id)
        clue = self._clue(session, request.clue_id)
        if not clue.discovered:
            raise ValueError("这件证据还没有被发现。")

        npc.relation.pressure = min(100, npc.relation.pressure + 18)
        npc.relation.fear = min(100, npc.relation.fear + 10)
        prompt = f"玩家向你展示证据【{clue.name}】：{clue.description}\n玩家说：{request.message}"
        answer = self._npc_reply(session, request.npc_id, prompt, confronted_clue=clue)
        session.chat.append(ChatMessage(speaker="你", role="player", content=f"展示【{clue.name}】：{request.message}"))
        session.chat.append(ChatMessage(speaker=npc.name, role="npc", content=answer))
        self._persist_session(session)
        return ActionResponse(game=session.view(), result=answer)

    def accuse(self, session_id: str, request: AccuseRequest) -> ActionResponse:
        session = self._session(session_id)
        session.phase = "review"
        suspect = self._npc(session, request.suspect_id)
        truth = session.script.truth
        correct = request.suspect_id == truth["killer_id"]
        score = 100 if correct else 0
        session.case.status = "solved" if correct else "mistaken"
        session.case.updated_label = "已侦破" if correct else "误判"
        result = (
            f"你的指控对象：{suspect.name}。评分：{score}/100。\n"
            f"真相：凶手是{suspect.name if correct else self._npc(session, truth['killer_id']).name}。作案手法：{truth['method']} 动机：{truth['motive']}"
        )
        session.chat.append(ChatMessage(speaker="你", role="player", content=f"我指控{suspect.name}。"))
        session.chat.append(ChatMessage(speaker="DM", role="dm", content=result))
        self._persist_session(session)
        return ActionResponse(game=session.view(), result=result)

    def clues_for(self, session: GameSession, location: str) -> list[Clue]:
        return [clue for clue in session.clues if clue.location == location]

    def _npc_reply(
        self,
        session: GameSession,
        npc_id: str,
        player_input: str,
        confronted_clue: Clue | None = None,
    ) -> str:
        npc = self._npc(session, npc_id)
        return session.agent(npc_id).reply(player_input, self._shared_context(session), confronted_clue)

    def _shared_context(self, session: GameSession) -> str:
        discovered = [f"{clue.name}: {clue.description}" for clue in session.clues if clue.discovered]
        return "；".join(discovered) if discovered else "尚未发现公开证据。"

    def _adjust_relation(self, npc: NPCState, message: str) -> None:
        hostile_words = ["撒谎", "凶手", "杀人犯", "威胁", "闭嘴"]
        gentle_words = ["请", "谢谢", "相信", "帮助", "拜托"]
        text = message.lower()
        if any(word in text for word in hostile_words):
            npc.relation.fear = min(100, npc.relation.fear + 12)
            npc.relation.pressure = min(100, npc.relation.pressure + 10)
            npc.relation.trust = max(0, npc.relation.trust - 8)
        if any(word in text for word in gentle_words):
            npc.relation.trust = min(100, npc.relation.trust + 8)
            npc.relation.fear = max(0, npc.relation.fear - 4)

    def _script(self, case_id: str, difficulty: Difficulty) -> CaseScript:
        if case_id == "dynamic":
            script = self._generate_case_with_llm(difficulty)
            self.generated_cases[script.summary.id] = deepcopy(script)
            return script
        if case_id in self.generated_cases:
            return deepcopy(self.generated_cases[case_id])
        raise KeyError("案件不存在。")

    def _restore(self) -> None:
        for case_id, payload in self.storage.load_case_scripts().items():
            script = CaseScript.from_payload(payload)
            self.generated_cases[case_id] = script
            self._index_script_memories(script)
        for session_id, payload in self.storage.load_sessions().items():
            case_id = payload["case"]["id"]
            try:
                script = self._script_for_restore(case_id)
            except KeyError:
                continue
            self.sessions[session_id] = GameSession.from_payload(payload, script, self.storage, self.qwen)

    def _script_for_restore(self, case_id: str) -> CaseScript:
        if case_id in self.generated_cases:
            return deepcopy(self.generated_cases[case_id])
        raise KeyError("案件不存在。")

    def _persist_script(self, script: CaseScript) -> None:
        self.generated_cases[script.summary.id] = deepcopy(script)
        self.storage.save_case_script(script.summary.id, script.to_payload())
        self._index_script_memories(script)

    def _persist_session(self, session: GameSession) -> None:
        self.storage.save_session(session.session_id, session.case.id, session.to_payload())

    def _index_script_memories(self, script: CaseScript) -> None:
        for npc_id, data in script.npcs.items():
            npc = data["state"]
            memories = [
                ("personality", f"姓名：{npc.name}；身份：{npc.title}；公开设定：{npc.public_profile}"),
                ("private_memory", str(data["private_memory"])),
            ]
            self.storage.upsert_npc_memories(script.summary.id, npc_id, memories)

    def _generate_case_with_llm(self, difficulty: Difficulty) -> CaseScript:
        if not self.qwen.enabled:
            raise ValueError("动态案件生成需要配置 DASHSCOPE_API_KEY。")

        case_id = f"case_{uuid4().hex[:8]}"
        created_label = f"创建于 {datetime.now().strftime('%H:%M')}"
        payload = self._generate_case_payload(case_id, difficulty)

        title = self._text(payload, "title", "未命名案件")
        intro = self._text(payload, "intro", "一桩新案件正在展开。")
        victim = self._text(payload, "victim", "死者")
        truth_payload = payload.get("truth") if isinstance(payload.get("truth"), dict) else {}
        locations = self._locations(payload)
        suspects_payload = self._list_of_dicts(payload, "suspects")[:3]
        clues_payload = self._list_of_dicts(payload, "clues")[:6]
        if len(suspects_payload) < 3 or len(clues_payload) < 4:
            raise ValueError("LLM 生成的案件结构不完整，请重试。")

        killer_id = self._text(truth_payload, "killer_id", "suspect_3")
        if killer_id not in {f"suspect_{index}" for index in range(1, 4)}:
            killer_id = "suspect_3"
        cover = scene_fallback(title[:8], victim[:10])
        summary = CaseSummary(
            id=case_id,
            title=title,
            difficulty=difficulty,
            created_label=created_label,
            updated_label="未侦破",
            days_left=3,
            cover_images=[cover, scene_fallback("证物", "关键线索"), scene_fallback("嫌疑人", "三人证词")],
        )
        scene_images = [
            SceneImage(id=f"{case_id}_scene_{index}", name=name, location=name, image_url=scene_fallback(name[:8], "可搜证"), caption=f"调查{name}。")
            for index, name in enumerate(locations[:3], start=1)
        ]
        npcs = {}
        for index, suspect in enumerate(suspects_payload, start=1):
            npc_id = f"suspect_{index}"
            name = self._text(suspect, "name", f"嫌疑人{index}")
            npc_title = self._text(suspect, "title", "嫌疑人")
            npcs[npc_id] = {
                "state": NPCState(
                    id=npc_id,
                    name=name,
                    title=npc_title,
                    public_profile=self._text(suspect, "public_profile", "与死者关系复杂，案发夜行踪存在疑点。"),
                    avatar_url=svg_data(name[:1], npc_title, ["#39434d", "#46343c", "#2f3f36"][index - 1], ["#e7b85f", "#d68aac", "#9fdfb4"][index - 1]),
                ),
                "private_memory": self._text(suspect, "private_memory", "你有自己的秘密，但不能主动泄露。"),
            }
        clues = []
        for index, clue_payload in enumerate(clues_payload, start=1):
            name = self._text(clue_payload, "name", f"线索{index}")
            location = self._text(clue_payload, "location", locations[(index - 1) % len(locations)])
            if location not in locations:
                location = locations[(index - 1) % len(locations)]
            clues.append(Clue(
                id=f"{case_id}_clue_{index}",
                name=name,
                location=location,
                description=self._text(clue_payload, "description", "这件证据仍需结合证词解读。"),
                image_url=scene_fallback(name[:8], location[:8]),
                is_key=bool(clue_payload.get("is_key", index <= 3)),
            ))
        truth = {
            "killer_id": killer_id,
            "method": self._text(truth_payload, "method", "真相仍待复盘。"),
            "motive": self._text(truth_payload, "motive", "动机仍待复盘。"),
        }
        return CaseScript(summary, intro, locations, scene_images, npcs, clues, truth)

    def _generate_case_payload(self, case_id: str, difficulty: Difficulty) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是剧本杀案件生成器。只输出一个合法 JSON，不要 Markdown，不要代码块。"
                    "案件必须公平可破：3 名嫌疑人、4-6 条线索、1 名真凶；NPC 私有记忆不能互相泄露。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"生成一个中文现代谋杀之谜案件，难度={difficulty}，case_id={case_id}。"
                    "JSON 结构必须为：{"
                    "\"title\":字符串,\"victim\":字符串,\"intro\":80到140字,"
                    "\"locations\":[4个可搜证地点],"
                    "\"suspects\":[{\"name\":姓名,\"title\":身份,\"public_profile\":公开简介,\"private_memory\":私有记忆}],"
                    "\"clues\":[{\"name\":证据名,\"location\":必须来自locations,\"description\":描述,\"is_key\":布尔}],"
                    "\"truth\":{\"killer_id\":\"suspect_1|suspect_2|suspect_3\",\"method\":作案手法,\"motive\":作案动机}"
                    "}。suspects 必须正好 3 个，顺序对应 suspect_1 到 suspect_3。"
                ),
            },
        ]
        raw = self.qwen.chat(messages, temperature=0.9)
        return self._parse_json_object(raw)

    def _parse_json_object(self, raw: str) -> dict:
        text = raw.strip()
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1)
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                text = text[start:end + 1]
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM 未返回合法案件 JSON，请重试。") from exc
        if not isinstance(payload, dict):
            raise ValueError("LLM 生成的案件不是 JSON 对象。")
        return payload

    def _locations(self, payload: dict) -> list[str]:
        items = payload.get("locations")
        if not isinstance(items, list):
            raise ValueError("LLM 生成的案件缺少 locations。")
        locations = [str(item).strip() for item in items if str(item).strip()]
        if len(locations) < 4:
            raise ValueError("LLM 至少需要生成 4 个搜证地点。")
        return locations[:4]

    def _list_of_dicts(self, payload: dict, key: str) -> list[dict]:
        items = payload.get(key)
        if not isinstance(items, list):
            raise ValueError(f"LLM 生成的案件缺少 {key}。")
        return [item for item in items if isinstance(item, dict)]

    def _text(self, payload: dict, key: str, default: str) -> str:
        value = payload.get(key) if isinstance(payload, dict) else None
        if value is None:
            return default
        text = str(value).strip()
        return text or default

    def _session(self, session_id: str) -> GameSession:
        if session_id not in self.sessions:
            raise KeyError("游戏会话不存在。")
        return self.sessions[session_id]

    def _npc(self, session: GameSession, npc_id: str) -> NPCState:
        if npc_id not in session.npcs:
            raise KeyError("NPC 不存在。")
        return session.npcs[npc_id]

    def _clue(self, session: GameSession, clue_id: str) -> Clue:
        for clue in session.clues:
            if clue.id == clue_id:
                return clue
        raise KeyError("证据不存在。")
