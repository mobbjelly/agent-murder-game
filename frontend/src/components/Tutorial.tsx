export interface TutorialStep {
  title: string
  body: string
  tip: string
}

export function getTutorialSteps(inGame: boolean): TutorialStep[] {
  if (!inGame) {
    return [
      {
        title: '欢迎来到 AI 剧本杀',
        body: '先点击“解决新案件”，选择难度后，系统会从为你载入一个案件。',
        tip: '建议第一次选择“中等”，体验最完整。',
      },
      {
        title: '案件会保存',
        body: '开始调查后的案件会出现在列表里。页面刷新或关闭后，案件仍可继续调查。',
        tip: '',
      },
    ]
  }
  return [
    {
      title: '阅读案情和线索',
      body: '中间纸条是案件简介和全部线索。先看地点、物品和矛盾点，建立初步时间线。',
      tip: '线索不是答案，需要结合 NPC 证词判断。',
    },
    {
      title: '查看场景大图',
      body: '左侧是案发现场。点击场景卡片可以查看大图，帮助你观察环境和细节。',
      tip: '现在场景点击只看图，不会触发搜证。',
    },
    {
      title: '质询嫌疑人',
      body: '右侧是嫌疑人。点击任意 NPC 后，可以用快捷问题或手动输入进行对话。',
      tip: '每个 NPC 都有独立记忆，问同样问题可能得到不同反应。',
    },
    {
      title: '用证据对质',
      body: '在 NPC 对话框里选择一条证据，再点击“对质”，NPC 会被迫解释这件证据。',
      tip: '关键证据通常会改变 NPC 的压力和防备程度。',
    },
    {
      title: '最终指控',
      body: '当你认为锁定真凶后，在对应 NPC 弹窗里点击“指控”。DM 会给出评分和真相复盘。',
      tip: '指控会揭示真相，建议调查充分后再点击。',
    },
  ]
}

export function TutorialToggle({
  enabled,
  onChange,
  floating = false,
}: {
  enabled: boolean
  onChange: (enabled: boolean) => void
  floating?: boolean
}) {
  return (
    <button
      className={floating ? 'tutorial-toggle floating' : 'tutorial-toggle'}
      onClick={() => onChange(!enabled)}
    >
      {enabled ? '关闭新手说明' : '开启新手说明'}
    </button>
  )
}

export function TutorialOverlay({
  step,
  index,
  total,
  onNext,
  onPrev,
  onClose,
}: {
  step: TutorialStep
  index: number
  total: number
  onNext: () => void
  onPrev: () => void
  onClose: () => void
}) {
  return (
    <aside className="tutorial-card">
      <button className="tutorial-close" onClick={onClose}>
        ×
      </button>
      <span className="tutorial-progress">
        {index + 1} / {total}
      </span>
      <h2>{step.title}</h2>
      <p>{step.body}</p>
      <small>{step.tip}</small>
      <div className="tutorial-actions">
        <button onClick={onPrev} disabled={index === 0}>
          上一步
        </button>
        <button onClick={onNext} disabled={index === total - 1}>
          下一步
        </button>
      </div>
    </aside>
  )
}
