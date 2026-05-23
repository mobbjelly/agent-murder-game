import { Difficulty } from '../api'

export function DifficultyModal({
  difficulty,
  loading,
  onChange,
  onClose,
  onConfirm,
}: {
  difficulty: Difficulty
  loading: boolean
  onChange: (difficulty: Difficulty) => void
  onClose: () => void
  onConfirm: () => void
}) {
  const options = [
    {
      value: 'easy' as Difficulty,
      icon: '☻',
      title: '简单',
      description: '嫌疑人更容易露出破绽，适合第一次体验。',
    },
    {
      value: 'medium' as Difficulty,
      icon: '♟',
      title: '中等',
      description: '线索逐步浮现，需要认真追问和对质。',
    },
    {
      value: 'hard' as Difficulty,
      icon: '☹',
      title: '困难',
      description: '谎言更隐蔽，需要反复施压才能发现漏洞。',
    },
  ]
  return (
    <div className="difficulty-backdrop" onClick={onClose}>
      <section
        className="difficulty-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <button className="difficulty-close" onClick={onClose}>
          ×
        </button>
        <h2>选择难度</h2>
        <p>难度决定了嫌疑人被侦测到的可能性有多大，以及他们是否会被发现。</p>
        <div className="difficulty-options">
          {options.map((option) => (
            <button
              key={option.value}
              className={
                difficulty === option.value
                  ? `difficulty-option ${option.value} active`
                  : `difficulty-option ${option.value}`
              }
              onClick={() => onChange(option.value)}
              type="button"
            >
              <span className="difficulty-icon">{option.icon}</span>
              <span className="difficulty-copy">
                <strong>{option.title}</strong>
                <small>{option.description}</small>
              </span>
              <span className="difficulty-radio" />
            </button>
          ))}
        </div>
        <button
          className="difficulty-confirm"
          onClick={onConfirm}
          disabled={loading}
        >
          {loading ? '载入中…' : '开始调查'}
        </button>
      </section>
    </div>
  )
}
