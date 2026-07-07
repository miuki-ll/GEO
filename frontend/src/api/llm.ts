import request from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface EngineItem {
  engine: string
  name: string
  default_model: string
  configured: boolean
  is_default: boolean
}

export interface UsageInfo {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  cost_cents?: number
}

export function listEngines() {
  return request.get<any, ApiResponse<EngineItem[]>>('/api/v1/llm/engines')
}

export function getUsage() {
  return request.get<any, ApiResponse<UsageInfo>>('/api/v1/llm/usage')
}
