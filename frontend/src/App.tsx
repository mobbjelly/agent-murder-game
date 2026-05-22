import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  api,
  assetUrl,
  CaseSummary,
  Difficulty,
  GameView,
  HealthResponse,
  NPCState,
} from './api'

const difficultyOptions: Difficulty[] = ['easy', 'medium', 'hard']

const generationSteps = ['分析题材', '生成嫌疑人', '埋设证据', '整理案情']
const lastSessionKey = 'agent-murder-game:last-session-id'

const quickQuestions = {
  relation: '请说明你和死者的真实关系。有没有利益冲突、旧怨或近期争执？',
  alibi: '案发时间你在哪里？请按时间顺序说明你的不在场证明，有谁可以证明？',
  detail: '你当时有注意到什么不寻常的细节？',
}

function App() {
  const [cases, setCases] = useState<CaseSummary[]>([])
  const [game, setGame] = useState<GameView | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [selectedNpcId, setSelectedNpcId] = useState<string>('')
  const [activeNpcId, setActiveNpcId] = useState<string | null>(null)
  const [selectedClueId, setSelectedClueId] = useState<string>('')
  const [previewScene, setPreviewScene] = useState<
    GameView['scene_images'][number] | null
  >(null)
  const [message, setMessage] = useState<string>('')
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [accuse, setAccuse] = useState({ suspect_id: '' })
  const [loading, setLoading] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [generationLabel, setGenerationLabel] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => setHealth({ ok: false }))
    api
      .cases()
      .then((items) => {
        setCases(items)
        setDifficulty(items[0]?.difficulty ?? 'medium')
      })
      .catch((err: Error) => setError(err.message))
    const lastSessionId = window.localStorage.getItem(lastSessionKey)
    if (lastSessionId) {
      api
        .game(lastSessionId)
        .then((restoredGame) => {
          setGame(restoredGame)
          setSelectedNpcId(restoredGame.npcs[0]?.id ?? '')
          setAccuse({ suspect_id: restoredGame.npcs[0]?.id ?? '' })
        })
        .catch(() => window.localStorage.removeItem(lastSessionKey))
    }
  }, [])

  const selectedNpc = useMemo(() => {
    return (
      game?.npcs.find((npc) => npc.id === selectedNpcId) ??
      game?.npcs[0] ??
      null
    )
  }, [game, selectedNpcId])

  const activeNpc = useMemo(() => {
    return game?.npcs.find((npc) => npc.id === activeNpcId) ?? null
  }, [game, activeNpcId])

  async function startNewGame(caseId: string, nextDifficulty = difficulty) {
    setLoading(true)
    setGenerationProgress(8)
    setGenerationLabel(caseId === 'dynamic' ? generationSteps[0] : '载入案件')
    setError('')
    let stepIndex = 0
    const progressTimer = window.setInterval(() => {
      stepIndex = Math.min(stepIndex + 1, generationSteps.length - 1)
      setGenerationLabel(
        caseId === 'dynamic' ? generationSteps[stepIndex] : '载入案件',
      )
      setGenerationProgress((current) => Math.min(current + 22, 90))
    }, 450)
    try {
      const nextGame = await api.newGame({
        case_id: caseId,
        difficulty: nextDifficulty,
      })
      setGenerationProgress(100)
      setGenerationLabel('案件已生成')
      setGame(nextGame)
      window.localStorage.setItem(lastSessionKey, nextGame.session_id)
      setCases((items) => mergeCase(items, nextGame.case))
      setSelectedNpcId(nextGame.npcs[0]?.id ?? '')
      setActiveNpcId(null)
      setSelectedClueId('')
      setAccuse({ suspect_id: nextGame.npcs[0]?.id ?? '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建案件失败')
    } finally {
      window.clearInterval(progressTimer)
      window.setTimeout(() => {
        setLoading(false)
        setGenerationProgress(0)
        setGenerationLabel('')
      }, 250)
    }
  }

  async function runAction(action: () => Promise<{ game: GameView }>) {
    if (!game) return
    setLoading(true)
    setError('')
    try {
      const result = await action()
      setGame(result.game)
      window.localStorage.setItem(lastSessionKey, result.game.session_id)
      setCases((items) => mergeCase(items, result.game.case))
    } catch (err) {
      setError(err instanceof Error ? err.message : '行动失败')
    } finally {
      setLoading(false)
    }
  }

  async function streamNpcMessage(npcId: string, text: string) {
    if (!game || loading) return
    const npc = game.npcs.find((item) => item.id === npcId)
    if (!npc) return
    setLoading(true)
    setError('')
    let streamedContent = ''
    try {
      await api.streamTalk(
        game.session_id,
        { npc_id: npcId, message: text },
        (event) => {
          if (event.type === 'game' && event.game) {
            setGame(event.game)
            window.localStorage.setItem(lastSessionKey, event.game.session_id)
            setCases((items) => mergeCase(items, event.game!.case))
            return
          }
          if (event.type === 'chunk' && event.content) {
            streamedContent += event.content
            setGame((current) => {
              if (!current) return current
              const chatWithoutDraft = current.chat.filter(
                (item) => item.role !== 'system' || item.speaker !== npc.name,
              )
              return {
                ...current,
                chat: [
                  ...chatWithoutDraft,
                  {
                    speaker: npc.name,
                    role: 'system',
                    content: streamedContent,
                  },
                ],
              }
            })
          }
          if (event.type === 'error')
            throw new Error(event.message ?? '流式对话失败')
        },
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : '流式对话失败')
    } finally {
      setLoading(false)
    }
  }

  function sendMessage(event?: FormEvent) {
    event?.preventDefault()
    const text = message.trim()
    if (!game || !selectedNpc || !text) return
    streamNpcMessage(selectedNpc.id, text)
    setMessage('')
  }

  function confront() {
    if (!game || !selectedNpc || !selectedClueId) return
    runAction(() =>
      api.confront(game.session_id, {
        npc_id: selectedNpc.id,
        clue_id: selectedClueId,
        message: message.trim() || '请解释这件证据。',
      }),
    )
    setMessage('')
  }

  function submitAccuse() {
    if (!game) return
    runAction(() => api.accuse(game.session_id, accuse))
  }

  async function deleteCase(caseId: string) {
    if (loading) return
    setLoading(true)
    setError('')
    try {
      await api.deleteCase(caseId)
      setCases((items) => items.filter((item) => item.id !== caseId))
      if (game?.case.id === caseId) {
        setGame(null)
        window.localStorage.removeItem(lastSessionKey)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除案件失败')
    } finally {
      setLoading(false)
    }
  }

  function askQuickQuestion(question: string) {
    if (!game || !activeNpcId || loading) return
    setSelectedNpcId(activeNpcId)
    streamNpcMessage(activeNpcId, question)
    setMessage('')
  }

  if (!game) {
    return (
      <main className="case-list-page">
        <section className="case-shell">
          {error && <div className="error-banner">{error}</div>}
          {loading && (
            <GlobalProgress
              value={generationProgress}
              label={generationLabel || '正在处理'}
            />
          )}

          <section className="new-case-panel top-new-case">
            <label>
              难度
              <select
                value={difficulty}
                onChange={(event) =>
                  setDifficulty(event.target.value as Difficulty)
                }
              >
                {difficultyOptions.map((item) => (
                  <option key={item} value={item}>
                    {difficultyLabel(item)}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="primary-action"
              onClick={() => startNewGame('dynamic', difficulty)}
              disabled={loading}
            >
              {loading ? '生成案件中…' : '生成新案件'}
            </button>
          </section>

          <section className="case-picker">
            {cases.map((item) => (
              <div key={item.id} className="case-row">
                <button
                  className="case-row-main"
                  onClick={() => startNewGame(item.id, item.difficulty)}
                  disabled={loading}
                >
                  <h2>{item.title}</h2>
                  <p>{item.created_label}</p>
                  <StatusPill status={item.status} label={item.updated_label} />
                  <span className="difficulty-pill">
                    {difficultyLabel(item.difficulty)}
                  </span>
                </button>
                <button
                  className="delete-case-button"
                  onClick={() => deleteCase(item.id)}
                  disabled={loading}
                >
                  删除
                </button>
              </div>
            ))}
          </section>

          <p className="case-count-tip">
            你还有 {cases.length} 个案件待侦破！
          </p>
        </section>
      </main>
    )
  }

  return (
    <main className="board-page">
      {error && <div className="error-banner floating">{error}</div>}
      <button className="back-button" onClick={() => setGame(null)}>
        ‹
      </button>
      <div className="case-title tape-label">{game.case.title}</div>

      <section className="scene-column">
        <h2 className="section-label">案发现场</h2>
        {game.scene_images.map((scene, index) => (
          <button
            key={scene.id}
            className="photo-card scene-photo"
            style={
              {
                '--tilt': `${index % 2 === 0 ? -4 : 3}deg`,
              } as React.CSSProperties
            }
            onClick={() => setPreviewScene(scene)}
            disabled={loading}
          >
            <img src={assetUrl(scene.image_url)} alt={scene.name} />
            <strong>{scene.name}</strong>
            <span>{scene.caption}</span>
            <small>点击查看大图</small>
          </button>
        ))}
      </section>

      <section className="story-note paper-card">
        <p>{game.intro}</p>
        <div className="evidence-strip">
          {game.discovered_clues.length === 0 && <span>暂无线索。</span>}
          {game.discovered_clues.map((clue) => (
            <button
              key={clue.id}
              className={
                selectedClueId === clue.id ? 'evidence active' : 'evidence'
              }
              onClick={() => setSelectedClueId(clue.id)}
            >
              {clue.image_url && (
                <img src={assetUrl(clue.image_url)} alt={clue.name} />
              )}
              <strong>{clue.name}</strong>
              <small>{clue.location}</small>
              <p>{clue.description}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="suspect-column">
        <h2 className="section-label suspects-label">嫌疑人</h2>
        {game.npcs.map((npc, index) => (
          <button
            key={npc.id}
            className={
              selectedNpcId === npc.id ? 'suspect-card active' : 'suspect-card'
            }
            style={
              { '--tilt': `${index === 1 ? 3 : -1}deg` } as React.CSSProperties
            }
            onClick={() => {
              setSelectedNpcId(npc.id)
              setActiveNpcId(npc.id)
              setAccuse({ suspect_id: npc.id })
            }}
          >
            <img src={assetUrl(npc.avatar_url)} alt={npc.name} />
            <strong>{npc.name}</strong>
            <p>{npc.public_profile}</p>
          </button>
        ))}
      </section>

      {activeNpc && selectedNpc && (
        <SuspectModal
          npc={activeNpc}
          clues={game.discovered_clues}
          chat={game.chat}
          selectedClueId={selectedClueId}
          message={message}
          loading={loading}
          onClose={() => setActiveNpcId(null)}
          onMessageChange={setMessage}
          onClueChange={setSelectedClueId}
          onSubmit={sendMessage}
          onConfront={confront}
          onAccuse={submitAccuse}
          onQuickQuestion={askQuickQuestion}
        />
      )}

      {previewScene && (
        <ScenePreviewModal
          scene={previewScene}
          onClose={() => setPreviewScene(null)}
        />
      )}
    </main>
  )
}

interface SuspectModalProps {
  npc: NPCState
  clues: GameView['discovered_clues']
  chat: GameView['chat']
  selectedClueId: string
  message: string
  loading: boolean
  onClose: () => void
  onMessageChange: (value: string) => void
  onClueChange: (value: string) => void
  onSubmit: (event?: FormEvent) => void
  onConfront: () => void
  onAccuse: () => void
  onQuickQuestion: (question: string) => void
}

function SuspectModal(props: SuspectModalProps) {
  const { npc, clues, chat, selectedClueId, message, loading } = props
  const modalChat = chat
    .filter(
      (item) =>
        item.target_npc_id === npc.id ||
        (!item.target_npc_id && item.speaker === npc.name),
    )
    .slice(-8)
  return (
    <div className="modal-backdrop">
      <section className="suspect-modal">
        <button className="close-button" onClick={props.onClose}>
          ×
        </button>
        <aside className="modal-side-panel">
          <div className="modal-profile compact-profile">
            <h2>{npc.name}</h2>
            <strong>{npc.title}</strong>
            <p>{npc.public_profile}</p>
            <div className="relation-bars">
              <span>信任 {npc.relation.trust}</span>
              <span>警惕 {npc.relation.fear}</span>
              <span>压力 {npc.relation.pressure}</span>
            </div>
          </div>
          <button
            className="final-accuse-button"
            onClick={props.onAccuse}
            disabled={loading}
          >
            指控 {npc.name}
          </button>
          <div className="modal-actions">
            <button
              type="button"
              onClick={() => props.onQuickQuestion(quickQuestions.relation)}
              disabled={loading}
            >
              <strong>人物关系</strong>
              <span>查看与死者的关系概况</span>
            </button>
            <button
              type="button"
              onClick={() => props.onQuickQuestion(quickQuestions.alibi)}
              disabled={loading}
            >
              <strong>不在场证明</strong>
              <span>追问案发时的具体行踪</span>
            </button>
            <button
              type="button"
              onClick={() => props.onQuickQuestion(quickQuestions.detail)}
              disabled={loading}
            >
              <strong>观察细节</strong>
              <span>询问当时注意到的不寻常细节</span>
            </button>
          </div>
        </aside>
        <section className="modal-chat-panel">
          <div className="dialog-panel">
            <ChatLog messages={modalChat} />
          </div>
          <form className="question-box" onSubmit={props.onSubmit}>
            <textarea
              value={message}
              onChange={(event) => props.onMessageChange(event.target.value)}
              placeholder="输入质询问题..."
            />
            <select
              value={selectedClueId}
              onChange={(event) => props.onClueChange(event.target.value)}
            >
              <option value="">选择证据</option>
              {clues.map((clue) => (
                <option key={clue.id} value={clue.id}>
                  {clue.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="accuse-button"
              onClick={props.onConfront}
              disabled={loading || !selectedClueId}
            >
              对质
            </button>
            <button type="submit" className="send-button" disabled={loading}>
              ↑
            </button>
          </form>
        </section>
      </section>
    </div>
  )
}

function ScenePreviewModal({
  scene,
  onClose,
}: {
  scene: GameView['scene_images'][number]
  onClose: () => void
}) {
  return (
    <div className="image-preview-backdrop" onClick={onClose}>
      <section
        className="image-preview-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        <img src={assetUrl(scene.image_url)} alt={scene.name} />
        <div className="image-preview-info">
          <h2>{scene.name}</h2>
          <p>{scene.caption}</p>
        </div>
      </section>
    </div>
  )
}

function ChatLog({
  messages,
  compact = false,
}: {
  messages: GameView['chat']
  compact?: boolean
}) {
  return (
    <div className={compact ? 'chat-log compact' : 'chat-log'}>
      {messages.length === 0 && <span className="empty-chat">暂无对话。</span>}
      {messages.map((item, index) => (
        <article
          key={`${item.speaker}-${index}-${item.content.slice(0, 8)}`}
          className={`chat-message ${item.role}`}
        >
          <strong>{item.speaker}</strong>
          <p>{item.content}</p>
        </article>
      ))}
    </div>
  )
}

function GlobalProgress({ value, label }: { value: number; label: string }) {
  return (
    <div className="global-progress" role="status" aria-live="polite">
      <div className="global-progress-header">
        <strong>{label}</strong>
        <span>{Math.round(value)}%</span>
      </div>
      <div className="global-progress-track">
        <div style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

function CoverStack({ images }: { images: string[] }) {
  return (
    <div className="cover-stack">
      {images.slice(0, 3).map((image, index) => (
        <img
          key={image}
          src={assetUrl(image)}
          alt="案件封面"
          style={{ left: `${index * 42}px` }}
        />
      ))}
    </div>
  )
}

function StatusPill({
  status,
  label,
}: {
  status: CaseSummary['status']
  label?: string
}) {
  return (
    <span className={`status-pill ${status}`}>
      {label ?? statusLabel(status)}
    </span>
  )
}

function mergeCase(items: CaseSummary[], nextCase: CaseSummary) {
  const exists = items.some((item) => item.id === nextCase.id)
  if (!exists) return [nextCase, ...items]
  return items.map((item) => (item.id === nextCase.id ? nextCase : item))
}

function statusLabel(value: CaseSummary['status']) {
  return {
    unsolved: '未侦破',
    solved: '已侦破',
    mistaken: '误判',
  }[value]
}

function difficultyLabel(value: Difficulty) {
  return {
    easy: '简单',
    medium: '中等',
    hard: '困难',
  }[value]
}

export default App
