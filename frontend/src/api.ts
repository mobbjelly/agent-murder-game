const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

export type Difficulty = 'easy' | 'medium' | 'hard'
export type CaseStatus = 'unsolved' | 'solved' | 'mistaken'
export type GamePhase = 'intro' | 'investigate' | 'accuse' | 'review'

export interface RelationState {
  trust: number
  fear: number
  pressure: number
}

export interface NPCState {
  id: string
  name: string
  title: string
  public_profile: string
  avatar_url: string
  relation: RelationState
}

export interface SceneImage {
  id: string
  name: string
  location: string
  image_url: string
  caption: string
}

export interface Clue {
  id: string
  name: string
  location: string
  description: string
  image_url: string
  is_key: boolean
  discovered: boolean
}

export interface CaseSummary {
  id: string
  title: string
  difficulty: Difficulty
  status: CaseStatus
  created_label: string
  updated_label: string
  days_left: number
  cover_images: string[]
}

export interface ChatMessage {
  speaker: string
  role: 'system' | 'player' | 'npc' | 'dm'
  content: string
}

export interface GameView {
  session_id: string
  case: CaseSummary
  phase: GamePhase
  intro: string
  locations: string[]
  scene_images: SceneImage[]
  npcs: NPCState[]
  discovered_clues: Clue[]
  chat: ChatMessage[]
}

export interface ActionResponse {
  game: GameView
  result: string
}

export interface HealthResponse {
  ok: boolean
  qwen_enabled?: boolean
  deepagents_enabled?: boolean
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail ?? 'Request failed')
  }
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<HealthResponse>('/health'),
  cases: () => request<CaseSummary[]>('/cases'),
  game: (sessionId: string) => request<GameView>(`/game/${sessionId}`),
  newGame: (payload: { case_id: string; difficulty: Difficulty }) => request<GameView>('/game/new', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  talk: (sessionId: string, payload: { npc_id: string; message: string }) => request<ActionResponse>(`/game/${sessionId}/talk`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  search: (sessionId: string, location: string) => request<ActionResponse>(`/game/${sessionId}/search`, {
    method: 'POST',
    body: JSON.stringify({ location }),
  }),
  confront: (sessionId: string, payload: { npc_id: string; clue_id: string; message: string }) => request<ActionResponse>(`/game/${sessionId}/confront`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  accuse: (sessionId: string, payload: { suspect_id: string }) => request<ActionResponse>(`/game/${sessionId}/accuse`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
}
