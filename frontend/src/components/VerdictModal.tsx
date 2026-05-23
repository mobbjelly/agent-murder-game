import { assetUrl, GameView, NPCState } from '../api'

export interface VerdictReport {
  accused: NPCState
  correct: boolean
  score: number
  result: string
  chat: GameView['chat']
  caseTitle: string
}

export function VerdictModal({
  report,
  onClose,
}: {
  report: VerdictReport
  onClose: () => void
}) {
  const strengths = buildStrengths(report.chat, report.correct)
  const weaknesses = buildWeaknesses(report.chat, report.correct)
  const dmSummary = extractTruth(report.result)
  return (
    <div className="verdict-backdrop">
      <section className="verdict-modal" role="dialog" aria-modal="true">
        <button className="verdict-close" onClick={onClose}>
          ×
        </button>
        <div className="verdict-portrait-wrap">
          <img
            className="verdict-portrait"
            src={assetUrl(report.accused.avatar_url)}
            alt={report.accused.name}
          />
          <span className={report.correct ? 'verdict-stamp solved' : 'verdict-stamp escaped'}>
            {report.correct ? 'SOLVED' : 'ESCAPED'}
          </span>
        </div>

        <div className="verdict-stars" aria-label={`${report.score} 分`}>
          {Array.from({ length: 5 }, (_, index) => (
            <span key={index} className={index < Math.ceil(report.score / 20) ? 'filled' : ''}>
              ★
            </span>
          ))}
        </div>

        <h2>
          {report.correct
            ? `${report.accused.name} 被成功定罪`
            : `${report.accused.name} 不是凶手`}
        </h2>
        <p className="verdict-case-title">{report.caseTitle}</p>

        <div className="verdict-score-row">
          <span className={report.correct ? 'primary' : 'danger'}>
            {report.correct ? '指控正确' : '指控错误'}
          </span>
          <span>{report.score}/100 分</span>
          <span>{countByRole(report.chat, 'player')} 次调查行动</span>
        </div>

        <section className="verdict-summary">
          <h3>主持人总结</h3>
          <p>{dmSummary}</p>
        </section>

        <section className="verdict-review">
          <h3>调查过程复盘</h3>
          <div>
            <article>
              <strong className="thumb good">👍</strong>
              {strengths.length > 0 ? (
                <ul>
                  {strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p>暂无明显优势</p>
              )}
            </article>
            <article>
              <strong className="thumb bad">👎</strong>
              <ul>
                {weaknesses.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          </div>
        </section>
      </section>
    </div>
  )
}

function extractTruth(result: string) {
  const truth = result.split('真相：')[1]?.trim()
  return truth || result
}

function countByRole(chat: GameView['chat'], role: GameView['chat'][number]['role']) {
  return chat.filter((item) => item.role === role).length
}

function buildStrengths(chat: GameView['chat'], correct: boolean) {
  const clueChallenges = chat.filter((item) => item.role === 'player' && item.content.includes('展示【')).length
  const questions = chat.filter((item) => item.role === 'player' && !item.content.includes('我指控')).length
  const strengths: string[] = []
  if (correct) strengths.push('锁定了真正凶手')
  if (clueChallenges > 0) strengths.push(`用 ${clueChallenges} 条证据进行对质`)
  if (questions >= 3) strengths.push('主动追问嫌疑人并积累证词')
  return strengths
}

function buildWeaknesses(chat: GameView['chat'], correct: boolean) {
  const clueChallenges = chat.filter((item) => item.role === 'player' && item.content.includes('展示【')).length
  const weaknesses: string[] = []
  if (!correct) weaknesses.push('指控了错误对象')
  if (clueChallenges === 0) weaknesses.push('没有用关键证据充分对质')
  if (countByRole(chat, 'player') < 4) weaknesses.push('调查轮次偏少，推理依据不足')
  if (weaknesses.length === 0) weaknesses.push('可以继续提高证词与物证之间的交叉验证')
  return weaknesses
}
