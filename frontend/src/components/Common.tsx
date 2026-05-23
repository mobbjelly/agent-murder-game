import { CaseSummary, GameView } from '../api'
import { statusLabel } from '../utils/cases'

export function ChatLog({
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

export function GlobalProgress({ value, label }: { value: number; label: string }) {
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

export function StatusPill({
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
