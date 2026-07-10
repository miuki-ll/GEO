import request from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface PersonaData {
  age_range: [number, number]
  genders: string[]
  cities: string[]
  core_needs: string[]
  decision_factors: string[]
  typical_queries: string[]
}

export interface CompetitorItem {
  name: string
  type: 'chain' | 'local' | 'studio'
  ai_mention_rate: number
  strengths: string[]
  weaknesses: string[]
  differentiator: string
}

export interface ScenarioItem {
  id?: number
  title: string
  user_query: string
  intent: string
  channel: string
  skill: string
  priority: number
  target_engines: string[]
  fact_refs?: number[]
}

export interface StrategyPackDraft {
  id: number
  version: string
  status: 'draft' | 'confirmed'
  persona: PersonaData
  competitors: CompetitorItem[]
  pain_points: { point: string; severity: number; evidence: string }[]
  scenarios: ScenarioItem[]
  channels: { name: string; weight: number; mode: string }[]
  created_at: string
  confirmed_at?: string
}

export function getDiagnosisPain() {
  return request.get<any, ApiResponse<any[]>>('/api/v1/user/diagnosis/pain')
}
export function getDiagnosisPersona() {
  return request.get<any, ApiResponse<PersonaData>>('/api/v1/user/diagnosis/persona')
}
export function getDiagnosisCompetitor() {
  return request.get<any, ApiResponse<CompetitorItem[]>>('/api/v1/user/diagnosis/competitor')
}

export function getStrategyPackDraft() {
  return request.get<any, ApiResponse<StrategyPackDraft>>('/api/v1/user/strategy-pack/draft')
}
export function confirmStrategyPack() {
  return request.post<any, ApiResponse<StrategyPackDraft>>('/api/v1/user/strategy-pack/confirm')
}
