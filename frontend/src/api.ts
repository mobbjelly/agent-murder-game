const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'
const ASSET_BASE = API_BASE.replace(/\/api\/?$/, '')

export function assetUrl(value: string) {
  if (!value || value.startsWith('data:') || /^https?:\/\//.test(value)) return value
  return `${ASSET_BASE}${value.startsWith('/') ? value : `/${value}`}`
}

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
  target_npc_id?: string | null
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
  qwen_image_enabled?: boolean
  qwen_image_model?: string
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
  deleteCase: (caseId: string) => request<{ ok: boolean; case_id: string }>(`/cases/${caseId}`, {
    method: 'DELETE',
  }),
  game: (sessionId: string) => request<GameView>(`/game/${sessionId}`),
  newGame: (payload: { case_id: string; difficulty: Difficulty }) => request<GameView>('/game/new', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  talk: (sessionId: string, payload: { npc_id: string; message: string }) => request<ActionResponse>(`/game/${sessionId}/talk`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  streamTalk: async (
    sessionId: string,
    payload: { npc_id: string; message: string },
    onEvent: (event: { type: string; content?: string; game?: GameView; message?: string }) => void,
  ) => {
    const response = await fetch(`${API_BASE}/game/${sessionId}/talk/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok || !response.body) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail ?? 'Request failed')
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() ?? ''
      for (const event of events) {
        const line = event.split('\n').find((item) => item.startsWith('data: '))
        if (line) onEvent(JSON.parse(line.slice(6)))
      }
    }
  },
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
