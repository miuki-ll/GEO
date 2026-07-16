import request from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface BuyerPersona {
  role: string
  age_range: number[]
  pain_tags: string[]
  decision_factors: string[]
  trust_triggers?: string[]
}

export interface ChannelMixed {
  name: string
  model_weight: number
  probe_weight: number
  mixed_weight: number
  scenario_count?: number
}

export interface ScenarioCandidate {
  id: string
  user_query: string
  intent: string
  channel: string
  skill: string
}

/** Five-zone draft view (PRD / B handbook §6) */
export interface StrategyPackDraftView {
  id?: number
  persona?: {
    buyer_personas?: BuyerPersona[]
    content_layout_plan?: Record<string, string>[]
  }
  competitors?: {
    profiles?: { name: string; type?: string; differentiation?: string }[]
    differentiation_brief?: string
    content_gaps?: string[]
  }
  scenarios?: {
    candidates?: ScenarioCandidate[]
    recommended_count?: number
    max?: number
  }
  channels?: ChannelMixed[]
  keywords?: { layers?: Record<string, { keyword: string; source?: string }[]> }
  kb_freshness?: { warning?: boolean; updated_at?: string }
  status?: string
  next_route?: string
}

/** @deprecated legacy shape — still accepted when normalizing API */
export interface ScenarioItem {
  id?: number | string
  title?: string
  user_query: string
  intent: string
  channel: string
  skill: string
  priority?: number
  target_engines?: string[]
  fact_refs?: number[]
}

export interface StrategyPackDraft {
  id: number
  version?: string
  status?: string
  persona?: any
  competitors?: any
  scenarios?: any
  channels?: any
  keywords?: any
  created_at?: string
  confirmed_at?: string
  next_route?: string
}

export function getStrategyPackDraft() {
  return request.get<any, ApiResponse<StrategyPackDraftView>>('/api/v1/user/strategy-pack/draft')
}

export function confirmStrategyPack(body?: {
  selected_scenarios: string[]
  channel_overrides?: Record<string, number>
  persona_confirmed?: boolean
  competitor_confirmed?: boolean
}) {
  return request.post<any, ApiResponse<StrategyPackDraftView>>(
    '/api/v1/user/strategy-pack/confirm',
    body || {},
  )
}
