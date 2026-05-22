from typing import Literal

from pydantic import BaseModel, Field


GamePhase = Literal["intro", "investigate", "accuse", "review"]
Difficulty = Literal["easy", "medium", "hard"]
CaseStatus = Literal["unsolved", "solved", "mistaken"]


class RelationState(BaseModel):
    trust: int = 45
    fear: int = 30
    pressure: int = 20


class NPCState(BaseModel):
    id: str
    name: str
    title: str
    public_profile: str
    avatar_url: str = ""
    relation: RelationState = Field(default_factory=RelationState)


class SceneImage(BaseModel):
    id: str
    name: str
    location: str
    image_url: str
    caption: str


class Clue(BaseModel):
    id: str
    name: str
    location: str
    description: str
    image_url: str = ""
    is_key: bool = False
    discovered: bool = False


class CaseSummary(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    status: CaseStatus = "unsolved"
    created_label: str
    updated_label: str
    days_left: int = 3
    cover_images: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    speaker: str
    role: Literal["system", "player", "npc", "dm"]
    content: str


class GameView(BaseModel):
    session_id: str
    case: CaseSummary
    phase: GamePhase
    intro: str
    locations: list[str]
    scene_images: list[SceneImage]
    npcs: list[NPCState]
    discovered_clues: list[Clue]
    chat: list[ChatMessage]


class NewGameRequest(BaseModel):
    case_id: str = "dynamic"
    difficulty: Difficulty = "medium"


class PlayerMessage(BaseModel):
    npc_id: str
    message: str


class SearchRequest(BaseModel):
    location: str


class ConfrontRequest(BaseModel):
    npc_id: str
    clue_id: str
    message: str = "请解释这件物证。"


class AccuseRequest(BaseModel):
    suspect_id: str


class ActionResponse(BaseModel):
    game: GameView
    result: str
