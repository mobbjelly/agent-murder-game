import { Difficulty } from '../api'

export const difficultyOptions: Difficulty[] = ['easy', 'medium', 'hard']

export const generationSteps = ['分析题材', '生成嫌疑人', '埋设证据', '整理案情']

export const tutorialModeKey = 'agent-murder-game:tutorial-mode'

export const quickQuestions = {
  relation: '请说明你和死者的真实关系。有没有利益冲突、旧怨或近期争执？',
  alibi: '案发时间你在哪里？请按时间顺序说明你的不在场证明，有谁可以证明？',
  detail: '你当时有注意到什么不寻常的细节？',
}
