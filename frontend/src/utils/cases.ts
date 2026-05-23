import { CaseSummary, Difficulty } from '../api'

export function mergeCase(items: CaseSummary[], nextCase: CaseSummary) {
  const exists = items.some((item) => item.id === nextCase.id)
  if (!exists) return [nextCase, ...items]
  return items.map((item) => (item.id === nextCase.id ? nextCase : item))
}

export function statusLabel(value: CaseSummary['status']) {
  return {
    unsolved: '未侦破',
    solved: '已侦破',
    mistaken: '误判',
  }[value]
}

export function difficultyLabel(value: Difficulty) {
  return {
    easy: '简单',
    medium: '中等',
    hard: '困难',
  }[value]
}
