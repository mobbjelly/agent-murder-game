import { useEffect, useRef } from 'react'
import { CaseSummary, GameView } from '../api'
import { statusLabel } from '../utils/cases'

export function ChatLog({
  messages,
  compact = false,
  thinkingLabel,
}: {
  messages: GameView['chat']
  compact?: boolean
  thinkingLabel?: string
}) {
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, thinkingLabel])

  return (
    <div className={compact ? 'chat-log compact' : 'chat-log'}>
      {messages.length === 0 && !thinkingLabel && (
        <span className="empty-chat">暂无对话。</span>
      )}
      {messages.map((item, index) => (
        <article
          key={`${item.speaker}-${index}-${item.content.slice(0, 8)}`}
          className={`chat-message ${item.role}`}
        >
          <strong>{item.speaker}</strong>
          <p>{item.content}</p>
        </article>
      ))}
      {thinkingLabel && (
        <article className="chat-message npc thinking" aria-live="polite">
          <strong>{thinkingLabel}</strong>
          <p>
            <span className="typing-dots" aria-label="思考中">
              <span />
              <span />
              <span />
            </span>
          </p>
        </article>
      )}
      <div ref={endRef} />
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
