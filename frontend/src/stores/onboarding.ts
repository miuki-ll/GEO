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

export interface OnboardingFormData {
  enterprise: {
    name: string
    industry: string
    license_no: string
    contact_name: string
    contact_phone: string
  }
  brand: { name: string; differentiator: string; slogan: string }
  stores: Array<{
    name: string
    city: string
    district: string
    address: string
    phone: string
    business_hours: string
  }>
  services: Array<{ name: string; description: string; category: string; price_hint: string }>
  competitors: string[]
  target_customers: string
  raw_inputs: string
  seed_facts: Array<{ title: string; content: string }>
  target_engines: string[]
}

function defaultFormData(): OnboardingFormData {
  return {
    enterprise: {
      name: 'XX 皮肤管理中心（XX路店）',
      industry: 'beauty_local',
      license_no: '',
      contact_name: 'Demo User',
      contact_phone: '',
    },
    brand: { name: '', differentiator: '', slogan: '' },
    stores: [
      {
        name: '',
        city: '',
        district: '',
        address: 'XX 市 XX 区 XX 路 88 号 2F',
        phone: '',
        business_hours: '10:00-21:30',
      },
    ],
    services: [{ name: '', description: '', category: '', price_hint: '' }],
    competitors: [],
    target_customers: '',
    raw_inputs: '',
    seed_facts: [
      { title: '门店资质', content: '本机构持有《卫生许可证》与《营业执照》，美容师均持资格证上岗。' },
      { title: '敏感肌项目说明', content: '敏感肌修护采用 XXX 植物萃取，经斑贴测试 0 过敏率。' },
      { title: '地址与营业时间', content: 'XX 市 XX 区 XX 路 88 号 2F，营业时间 10:00-21:30，全年无休。' },
    ],
    target_engines: ['doubao'],
  }
}

interface OnboardingState {
  currentStep: number
  status: 'idle' | 'pending' | 'running' | 'done' | 'failed'
  taskId: number | null
  progress: number
  message: string
  packDraft: StrategyPackDraft | null
  profileData: any
  kbData: any
  formData: OnboardingFormData
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
    formData: defaultFormData(),
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
    setStatus(s: OnboardingStatus['status'] | 'idle', extra: Partial<OnboardingState> = {}) {
      this.status = s as OnboardingState['status']
      Object.assign(this, extra)
    },
    reset() {
      this.$reset()
      this.formData = defaultFormData()
    },
  },
  persist: {
    key: 'geo-onboarding',
    pick: ['currentStep', 'formData', 'taskId', 'status', 'progress'],
  },
})
