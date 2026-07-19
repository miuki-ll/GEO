import request from '@/utils/request'
import type { ApiResponse } from '@/types'

// ── A5 OnboardingRunRequest（对齐 backend/app/schemas/onboarding.py）──

export interface EnterpriseInfo {
  name: string
  industry?: string
  license_no?: string
  contact_name?: string
  contact_phone?: string
}

export interface BrandInfo {
  name: string
  differentiator?: string
  slogan?: string
}

export interface StoreInfo {
  name: string
  city?: string
  district?: string
  address?: string
  phone?: string
  business_hours?: string
  is_primary?: boolean
}

export interface ServiceInfo {
  name: string
  description?: string
  category?: string
  price_hint?: string
  duration_minutes?: number
}

export interface SeedFact {
  title: string
  content: string
}

export interface OnboardingRunRequest {
  enterprise: EnterpriseInfo
  brand?: BrandInfo
  stores: StoreInfo[]
  services: ServiceInfo[]
  competitors: string[]
  target_customers: string
  raw_inputs: string
  seed_facts: SeedFact[]
  target_engines: string[]
  search_enabled: boolean
}

export interface OnboardingTaskResponse {
  task_id: number
  status: string
  progress_pct: number
  progress_message: string
  step: string
  result?: any
}

// ── API 函数 ──

export function runOnboarding(data: OnboardingRunRequest) {
  return request.post<any, ApiResponse<OnboardingTaskResponse>>('/api/v1/user/onboarding/run', data)
}

/** 创建 SSE 连接监听入驻进度。返回 EventSource，调用方负责 close。 */
export function subscribeOnboardingEvents(taskId: number): EventSource {
  const base = import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_BASE_URL || ''
  const token = localStorage.getItem('geo-user')
    ? JSON.parse(localStorage.getItem('geo-user') || '{}').token || ''
    : ''
  // SSE 需要 token 鉴权，通过 query param 传递（FastAPI SSE 不支持 header）
  const url = `${base}/api/v1/user/onboarding/events/${taskId}?token=${encodeURIComponent(token)}`
  return new EventSource(url)
}
