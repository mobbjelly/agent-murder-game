import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  api,
  assetUrl,
  CaseSummary,
  Difficulty,
  GameView,
  getClientId,
  HealthResponse,
} from './api'
import { AdminPage } from './components/AdminPage'
import { DifficultyModal } from './components/DifficultyModal'
import { GlobalProgress, StatusPill } from './components/Common'
import { ScenePreviewModal } from './components/ScenePreviewModal'
import { SuspectModal } from './components/SuspectModal'
import {
  getTutorialSteps,
  TutorialOverlay,
  TutorialToggle,
} from './components/Tutorial'
import { generationSteps, tutorialModeKey } from './constants/game'
import { difficultyLabel, mergeCase } from './utils/cases'

function App() {
  const [cases, setCases] = useState<CaseSummary[]>([])
  const [isAdminPage] = useState(() => window.location.pathname === '/admin')
  const [lastSessionKey] = useState(
    () => `agent-murder-game:last-session-id:${getClientId()}`,
  )
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
  const [difficultyModalOpen, setDifficultyModalOpen] = useState(false)
  const [accuse, setAccuse] = useState({ suspect_id: '' })
  const [loading, setLoading] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [generationLabel, setGenerationLabel] = useState('')
  const [actionResult, setActionResult] = useState<{
    npcId: string
    content: string
  } | null>(null)
  const [tutorialEnabled, setTutorialEnabled] = useState(
    () => window.localStorage.getItem(tutorialModeKey) !== 'off',
  )
  const [tutorialStep, setTutorialStep] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => setHealth({ ok: false }))
    const loadCases = isAdminPage ? api.adminCases : api.cases
    loadCases()
      .then((items) => {
        setCases(items)
        setDifficulty(items[0]?.difficulty ?? 'medium')
      })
      .catch((err: Error) => setError(err.message))
    if (isAdminPage) return
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
  }, [isAdminPage, lastSessionKey])

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

  const tutorialSteps = useMemo(() => getTutorialSteps(Boolean(game)), [game])
  const currentTutorial =
    tutorialSteps[Math.min(tutorialStep, tutorialSteps.length - 1)]

  function setTutorialMode(enabled: boolean) {
    setTutorialEnabled(enabled)
    window.localStorage.setItem(tutorialModeKey, enabled ? 'on' : 'off')
    setTutorialStep(0)
  }

  async function startNewGame(
    caseId?: string | null,
    nextDifficulty = difficulty,
  ) {
    setLoading(true)
    setGenerationProgress(12)
    setGenerationLabel('匹配案件中')
    setError('')
    let stepIndex = 0
    const progressTimer = window.setInterval(() => {
      stepIndex = Math.min(stepIndex + 1, generationSteps.length - 1)
      setGenerationLabel(stepIndex > 1 ? '载入案件' : '匹配案件')
      setGenerationProgress((current) => Math.min(current + 22, 90))
    }, 450)
    try {
      const nextGame = await api.newGame({
        case_id: caseId,
        difficulty: nextDifficulty,
      })
      setGenerationProgress(100)
      setGenerationLabel('案件已载入')
      setGame(nextGame)
      window.localStorage.setItem(lastSessionKey, nextGame.session_id)
      setCases((items) => mergeCase(items, nextGame.case))
      setSelectedNpcId(nextGame.npcs[0]?.id ?? '')
      setActiveNpcId(null)
      setSelectedClueId('')
      setAccuse({ suspect_id: nextGame.npcs[0]?.id ?? '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '载入案件失败')
    } finally {
      window.clearInterval(progressTimer)
      window.setTimeout(() => {
        setLoading(false)
        setGenerationProgress(0)
        setGenerationLabel('')
      }, 250)
    }
  }

  async function generateCaseForAdmin(nextDifficulty = difficulty) {
    setLoading(true)
    setGenerationProgress(8)
    setGenerationLabel(generationSteps[0])
    setError('')
    let stepIndex = 0
    const progressTimer = window.setInterval(() => {
      stepIndex = Math.min(stepIndex + 1, generationSteps.length - 1)
      setGenerationLabel(generationSteps[stepIndex])
      setGenerationProgress((current) => Math.min(current + 22, 90))
    }, 900)
    try {
      const nextCase = await api.generateCase({ difficulty: nextDifficulty })
      setCases((items) => mergeCase(items, nextCase))
      setGenerationProgress(100)
      setGenerationLabel('预生成完成')
    } catch (err) {
      setError(err instanceof Error ? err.message : '预生成案件失败')
    } finally {
      window.clearInterval(progressTimer)
      window.setTimeout(() => {
        setLoading(false)
        setGenerationProgress(0)
        setGenerationLabel('')
      }, 250)
    }
  }

  async function runAction(
    action: () => Promise<{ game: GameView; result?: string }>,
    resultNpcId?: string,
  ) {
    if (!game) return
    setLoading(true)
    setError('')
    try {
      const result = await action()
      setGame(result.game)
      if (result.result && resultNpcId) {
        setActionResult({ npcId: resultNpcId, content: result.result })
      }
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
    if (!game || !activeNpcId) return
    runAction(
      () => api.accuse(game.session_id, { suspect_id: activeNpcId }),
      activeNpcId,
    )
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

  async function deleteAdminCase(caseId: string) {
    if (loading) return
    setLoading(true)
    setError('')
    try {
      await api.deleteAdminCase(caseId)
      setCases((items) => items.filter((item) => item.id !== caseId))
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

  if (isAdminPage) {
    return (
      <AdminPage
        cases={cases}
        difficulty={difficulty}
        loading={loading}
        error={error}
        progress={generationProgress}
        progressLabel={generationLabel}
        onDifficultyChange={setDifficulty}
        onGenerate={() => generateCaseForAdmin(difficulty)}
        onDelete={deleteAdminCase}
      />
    )
  }

  if (!game) {
    return (
      <main className="case-list-page">
        <section className="case-shell">
          <TutorialToggle
            enabled={tutorialEnabled}
            onChange={setTutorialMode}
            floating
          />
          {error && <div className="error-banner">{error}</div>}
          {loading && (
            <GlobalProgress
              value={generationProgress}
              label={generationLabel || '正在处理'}
            />
          )}

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
                {item.updated_label !== '待领取' && (
                  <button
                    className="delete-case-button"
                    onClick={() => deleteCase(item.id)}
                    disabled={loading}
                  >
                    删除
                  </button>
                )}
              </div>
            ))}
          </section>

          <p className="case-count-tip">
            {cases.length > 0
              ? `已为你准备 ${cases.length} 个案件。`
              : '暂无可用案件。'}
          </p>
          <button
            className="primary-action solve-new-case-button"
            onClick={() => setDifficultyModalOpen(true)}
            disabled={loading}
          >
            {loading ? '载入案件中…' : '解决新案件'}
          </button>
        </section>
        {difficultyModalOpen && (
          <DifficultyModal
            difficulty={difficulty}
            loading={loading}
            onChange={setDifficulty}
            onClose={() => setDifficultyModalOpen(false)}
            onConfirm={() => {
              setDifficultyModalOpen(false)
              startNewGame(null, difficulty)
            }}
          />
        )}
        {tutorialEnabled && currentTutorial && (
          <TutorialOverlay
            step={currentTutorial}
            index={tutorialStep}
            total={tutorialSteps.length}
            onNext={() =>
              setTutorialStep((current) =>
                Math.min(current + 1, tutorialSteps.length - 1),
              )
            }
            onPrev={() =>
              setTutorialStep((current) => Math.max(current - 1, 0))
            }
            onClose={() => setTutorialMode(false)}
          />
        )}
      </main>
    )
  }

  return (
    <main className="board-page">
      {error && <div className="error-banner floating">{error}</div>}
      <TutorialToggle
        enabled={tutorialEnabled}
        onChange={setTutorialMode}
        floating
      />
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
          </button>
        ))}
      </section>

      <section className="story-note paper-card">
        <div className="case-brief">
          <h2>案情简介</h2>
          <p>{game.intro}</p>
        </div>
        <div className="clue-header">
          <h2>证据线索</h2>
          <span>{game.discovered_clues.length} 条</span>
        </div>
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
              <div>
                <strong>{clue.name}</strong>
                <small>{clue.location}</small>
              </div>
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
          actionResult={
            actionResult?.npcId === activeNpc.id ? actionResult.content : ''
          }
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
      {tutorialEnabled && currentTutorial && !activeNpc && !previewScene && (
        <TutorialOverlay
          step={currentTutorial}
          index={tutorialStep}
          total={tutorialSteps.length}
          onNext={() =>
            setTutorialStep((current) =>
              Math.min(current + 1, tutorialSteps.length - 1),
            )
          }
          onPrev={() => setTutorialStep((current) => Math.max(current - 1, 0))}
          onClose={() => setTutorialMode(false)}
        />
      )}
    </main>
  )
}

export default App
