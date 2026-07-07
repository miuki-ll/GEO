import { defineStore } from 'pinia'
import type { ChainStep, OnboardingStatus } from '@/types'
import type { StrategyPackDraft } from '@/api/strategy'

export const ONBOARDING_STEPS: ChainStep[] = [
  { key: 'profile', title: '企业信息', desc: '基本资料与行业' },
  { key: 'kb_seed', title: '知识种子', desc: '资质/项目/地址 FAQ' },
  { key: 'persona', title: '用户画像', desc: '目标客群分析' },
  { key: 'competitor', title: '竞品分析', desc: '差异化定位' },
  { key: 'scenarios', title: '场景挖掘', desc: '真实问答问题' },
  { key: 'channels', title: '渠道权重', desc: 'AUTO / SEMI / GUIDED' },
  { key: 'confirm', title: '方案包确认', desc: '人工闸门 1/2' },
  { key: 'first_content', title: '首轮内容', desc: 'FAQ + 1 小红书' },
]

interface OnboardingState {
  currentStep: number
  status: 'idle' | 'pending' | 'running' | 'done' | 'failed'
  taskId: string | null
  progress: number
  message: string
  packDraft: StrategyPackDraft | null
  profileData: any
  kbData: any
}

export const useOnboardingStore = defineStore('onboarding', {
  state: (): OnboardingState => ({
    currentStep: 0,
    status: 'idle',
    taskId: null,
    progress: 0,
    message: '',
    packDraft: null,
    profileData: {},
    kbData: {},
  }),
  getters: {
    steps: () => ONBOARDING_STEPS,
    canNext: (s) => s.currentStep < ONBOARDING_STEPS.length - 1,
    canPrev: (s) => s.currentStep > 0,
  },
  actions: {
    setStep(i: number) {
      if (i >= 0 && i < ONBOARDING_STEPS.length) {
        this.currentStep = i
      }
    },
    next() {
      if (this.canNext) this.currentStep++
    },
    prev() {
      if (this.canPrev) this.currentStep--
    },
    setStatus(s: OnboardingStatus['status'], extra: Partial<OnboardingState> = {}) {
      this.status = s
      Object.assign(this, extra)
    },
    reset() {
      this.$reset()
    },
  },
  persist: {
    key: 'geo-onboarding',
    pick: ['currentStep', 'packDraft', 'profileData', 'kbData'],
  },
})
