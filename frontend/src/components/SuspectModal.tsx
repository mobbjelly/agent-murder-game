import { FormEvent } from 'react'
import { GameView, NPCState } from '../api'
import { quickQuestions } from '../constants/game'
import { ChatLog } from './Common'

interface SuspectModalProps {
  npc: NPCState
  clues: GameView['discovered_clues']
  chat: GameView['chat']
  selectedClueId: string
  message: string
  loading: boolean
  thinking: boolean
  actionResult: string
  onClose: () => void
  onMessageChange: (value: string) => void
  onClueChange: (value: string) => void
  onSubmit: (event?: FormEvent) => void
  onConfront: () => void
  onAccuse: () => void
  onQuickQuestion: (question: string) => void
}

export function SuspectModal(props: SuspectModalProps) {
  const {
    npc,
    clues,
    chat,
    selectedClueId,
    message,
    loading,
    thinking,
    actionResult,
  } = props
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
            <ChatLog
              messages={modalChat}
              thinkingLabel={thinking ? `${npc.name} 正在思考` : undefined}
            />
            {actionResult && (
              <article className="action-result-card">
                <strong>DM</strong>
                <p>{actionResult}</p>
              </article>
            )}
          </div>
          <form className="question-box" onSubmit={props.onSubmit}>
            <textarea
              value={message}
              onChange={(event) => props.onMessageChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  props.onSubmit()
                }
              }}
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
