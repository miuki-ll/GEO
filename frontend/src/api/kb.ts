import request from '@/utils/request'
import type { ApiResponse, PaginationParams, KBFactItem, KBFaqItem } from '@/types'

export interface KBItemBase {
  id?: number
  enterprise_id?: number
  created_at?: string
  updated_at?: string
  metadata?: Record<string, any>
}

export interface FactForm {
  title: string
  content: string
  source_type?: string
  source_ref?: string
  category?: string
  tags?: string[]
  verified?: boolean
  metadata?: Record<string, any>
}

export interface FaqForm {
  question: string
  answer: string
  category?: string
  tags?: string[]
  fact_refs?: number[]
  verified?: boolean
  metadata?: Record<string, any>
}

export interface SignalForm {
  signal_type: string
  content: string
  source?: string
  confidence?: number
  fact_refs?: number[]
  status?: string
  metadata?: Record<string, any>
}

export interface ExternalForm {
  url?: string
  title?: string
  source_platform?: string
  content?: string
  summary?: string
  status?: string
  fact_refs?: number[]
  metadata?: Record<string, any>
}

export interface KBSummary {
  facts: number
  faqs: number
  signals: number
  externals: number
  verified_facts: number
  verified_faqs: number
  last_updated?: string
}

export function getKBSummary() {
  return request.get<any, ApiResponse<KBSummary>>('/api/v1/user/kb/summary')
}

// Facts
export function listFacts(params: PaginationParams & { category?: string; verified?: boolean; source_type?: string } = {}) {
  return request.get<any, ApiResponse<KBFactItem[]>>('/api/v1/user/kb/facts', { params })
}
export function createFact(data: FactForm) {
  return request.post<any, ApiResponse<KBFactItem>>('/api/v1/user/kb/facts', data)
}
export function getFact(id: number) {
  return request.get<any, ApiResponse<KBFactItem>>(`/api/v1/user/kb/facts/${id}`)
}
export function updateFact(id: number, data: Partial<FactForm>) {
  return request.put<any, ApiResponse<KBFactItem>>(`/api/v1/user/kb/facts/${id}`, data)
}
export function deleteFact(id: number) {
  return request.delete<any, ApiResponse<any>>(`/api/v1/user/kb/facts/${id}`)
}
export function bulkDeleteFacts(ids: number[]) {
  return request.post<any, ApiResponse<any>>('/api/v1/user/kb/facts/bulk-delete', { ids })
}

// FAQs
export function listFaqs(params: PaginationParams & { category?: string; verified?: boolean } = {}) {
  return request.get<any, ApiResponse<KBFaqItem[]>>('/api/v1/user/kb/faqs', { params })
}
export function createFaq(data: FaqForm) {
  return request.post<any, ApiResponse<KBFaqItem>>('/api/v1/user/kb/faqs', data)
}
export function updateFaq(id: number, data: Partial<FaqForm>) {
  return request.put<any, ApiResponse<KBFaqItem>>(`/api/v1/user/kb/faqs/${id}`, data)
}
export function deleteFaq(id: number) {
  return request.delete<any, ApiResponse<any>>(`/api/v1/user/kb/faqs/${id}`)
}

// Signals
export function listSignals(params: PaginationParams & { signal_type?: string; status?: string } = {}) {
  return request.get<any, ApiResponse<any[]>>('/api/v1/user/kb/signals', { params })
}
export function createSignal(data: SignalForm) {
  return request.post<any, ApiResponse<any>>('/api/v1/user/kb/signals', data)
}
export function updateSignal(id: number, data: Partial<SignalForm>) {
  return request.put<any, ApiResponse<any>>(`/api/v1/user/kb/signals/${id}`, data)
}
export function deleteSignal(id: number) {
  return request.delete<any, ApiResponse<any>>(`/api/v1/user/kb/signals/${id}`)
}

// Externals
export function listExternals(params: PaginationParams & { source_platform?: string; status?: string } = {}) {
  return request.get<any, ApiResponse<any[]>>('/api/v1/user/kb/externals', { params })
}
export function createExternal(data: ExternalForm) {
  return request.post<any, ApiResponse<any>>('/api/v1/user/kb/externals', data)
}
export function updateExternal(id: number, data: Partial<ExternalForm>) {
  return request.put<any, ApiResponse<any>>(`/api/v1/user/kb/externals/${id}`, data)
}
export function deleteExternal(id: number) {
  return request.delete<any, ApiResponse<any>>(`/api/v1/user/kb/externals/${id}`)
}
