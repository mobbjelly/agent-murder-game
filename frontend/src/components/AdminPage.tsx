import { CaseSummary, Difficulty } from '../api'
import { difficultyOptions } from '../constants/game'
import { difficultyLabel } from '../utils/cases'
import { GlobalProgress } from './Common'

export function AdminPage({
  cases,
  difficulty,
  loading,
  error,
  progress,
  progressLabel,
  onDifficultyChange,
  onGenerate,
  onDelete,
}: {
  cases: CaseSummary[]
  difficulty: Difficulty
  loading: boolean
  error: string
  progress: number
  progressLabel: string
  onDifficultyChange: (difficulty: Difficulty) => void
  onGenerate: () => void
  onDelete: (caseId: string) => void
}) {
  const counts = difficultyOptions.map((item) => ({
    difficulty: item,
    count: cases.filter((caseItem) => caseItem.difficulty === item).length,
  }))
  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <span>Developer Console</span>
            <h1>案件预生成后台</h1>
            <p>玩家点击“解决新案件”时，只会从这里预生成好的同难度案件中选择。</p>
          </div>
          <a href="/" className="admin-back-link">
            返回游戏
          </a>
        </header>

        {error && <div className="error-banner">{error}</div>}
        {loading && (
          <GlobalProgress value={progress} label={progressLabel || '正在预生成'} />
        )}

        <section className="admin-generate-card">
          <div>
            <h2>生成新案件</h2>
            <p>选择难度后会调用 LLM 生成案件文本、NPC 记忆和图片资源，并写入数据库。</p>
          </div>
          <select
            value={difficulty}
            onChange={(event) => onDifficultyChange(event.target.value as Difficulty)}
            disabled={loading}
          >
            {difficultyOptions.map((item) => (
              <option key={item} value={item}>
                {difficultyLabel(item)}
              </option>
            ))}
          </select>
          <button className="primary-action admin-generate-button" onClick={onGenerate} disabled={loading}>
            {loading ? '生成中…' : '预生成案件'}
          </button>
        </section>

        <section className="admin-stats-grid">
          {counts.map((item) => (
            <div key={item.difficulty} className="admin-stat-card">
              <strong>{item.count}</strong>
              <span>{difficultyLabel(item.difficulty)}案件</span>
            </div>
          ))}
        </section>

        <section className="admin-case-list">
          <h2>案件库存</h2>
          {cases.length === 0 && <p className="admin-empty">暂无预生成案件。</p>}
          {cases.map((item) => (
            <div key={item.id} className="admin-case-row">
              <div>
                <h3>{item.title}</h3>
                <p>
                  {difficultyLabel(item.difficulty)} · {item.created_label} · {item.updated_label}
                </p>
              </div>
              <button onClick={() => onDelete(item.id)} disabled={loading}>
                删除
              </button>
            </div>
          ))}
        </section>
      </section>
    </main>
  )
}
