import request from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface OnboardingRunRequest {
  industry?: string
  mode?: 'quick' | 'full'
}

export interface OnboardingStatus {
  task_id: string
  status: 'pending' | 'running' | 'done' | 'failed'
  progress_pct: number
  progress_message: string
  step: number
  total_steps: number
  result?: {
    pack_id?: number
    persona?: any
    scenarios?: any[]
  }
  error?: string
}

export function runOnboarding(data: OnboardingRunRequest = {}) {
  return request.post<any, ApiResponse<OnboardingStatus>>('/api/v1/user/onboarding/run', data)
}

export function getOnboardingStatus(taskId: string) {
  return request.get<any, ApiResponse<OnboardingStatus>>(`/api/v1/user/onboarding/status/${taskId}`)
}
