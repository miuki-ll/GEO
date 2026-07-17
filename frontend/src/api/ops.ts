import request from '@/utils/request'
import type { ApiResponse, PaginationParams, ContentDraftItem, PublishTaskItem, MonitorResultItem, DashboardKpi } from '@/types'

export interface ProduceRequest {
  scenario_ids?: number[]
  mode?: 'gap' | 'all'
}

export interface AgentTask {
  id: string
  task_type: string
  graph_name: string
  status: 'pending' | 'running' | 'done' | 'failed'
  progress_pct: number
  progress_message: string
  output_data?: any
  error?: string
}

const U = '/api/v1/user'
const A = '/api/v1/agent'

// content
export function listDrafts(params: PaginationParams & { status?: string; channel?: string } = {}) {
  return request.get<any, ApiResponse<ContentDraftItem[]>>(`${U}/content/drafts`, { params })
}
export function getDraft(id: number) {
  return request.get<any, ApiResponse<ContentDraftItem>>(`${U}/content/drafts/${id}`)
}
export function createDraft(data: Partial<ContentDraftItem>) {
  return request.post<any, ApiResponse<ContentDraftItem>>(`${U}/content/drafts`, data)
}
export function updateDraft(id: number, data: Partial<ContentDraftItem>) {
  return request.put<any, ApiResponse<ContentDraftItem>>(`${U}/content/drafts/${id}`, data)
}
export function bulkApproveDrafts(ids: number[]) {
  return request.post<any, ApiResponse<any>>(`${U}/content/drafts/bulk-approve`, { ids })
}
export function approveDraft(id: number, note?: string) {
  return request.post<any, ApiResponse<any>>(`${U}/content/drafts/${id}/approve`, null, {
    params: note ? { note } : undefined,
  })
}
export function rejectDraft(id: number, reason?: string) {
  return request.post<any, ApiResponse<any>>(`${U}/content/drafts/${id}/reject`, { reason: reason || '' })
}
export function runMachineReview(id: number) {
  return request.post<any, ApiResponse<any>>(`${U}/content/drafts/${id}/machine-review`)
}
export function triggerContentProduce(data: ProduceRequest = {}) {
  return request.post<any, ApiResponse<AgentTask>>(`${A}`, {
    task_type: 'content_produce',
    graph_name: 'content_pipeline',
    input_data: data,
  })
}

// publish
export function listPublishTasks(params: PaginationParams & { status?: string; channel?: string } = {}) {
  return request.get<any, ApiResponse<PublishTaskItem[]>>(`${U}/publish`, { params })
}
export function createPublishTask(data: Partial<PublishTaskItem> & { draft_id: number }) {
  return request.post<any, ApiResponse<PublishTaskItem>>(`${U}/publish`, data)
}
export function runPublish(task_ids: number[]) {
  return request.post<any, ApiResponse<{ started: number; results: any[] }>>(`${U}/publish/run`, {
    task_ids,
  })
}
export function autoPublish(taskId: number) {
  return request.post<any, ApiResponse<PublishTaskItem>>(`${U}/publish/${taskId}/auto`)
}
export function retryPublishTask(taskId: number) {
  return request.post<any, ApiResponse<PublishTaskItem>>(`${U}/publish/${taskId}/retry`)
}
export function semiPublish(taskId: number, published_url: string, published_id?: string) {
  return request.post<any, ApiResponse<PublishTaskItem>>(`${U}/publish/${taskId}/semi`, {
    published_url,
    published_id,
  })
}

// monitor
export function listCore(params: PaginationParams = {}) {
  return request.get<any, ApiResponse<MonitorResultItem[]>>(`${U}/monitor/core`, { params })
}
export function listProbe(params: PaginationParams = {}) {
  return request.get<any, ApiResponse<MonitorResultItem[]>>(`${U}/monitor/probe`, { params })
}
export function triggerMonitor(pool: 'core' | 'probe') {
  return request.post<any, ApiResponse<AgentTask>>(`${U}/monitor/trigger`, { pool })
}

// outcomes
export function getDashboard(period: 'week' | 'month' | 'quarter' = 'week') {
  return request.get<any, ApiResponse<DashboardKpi>>(`${U}/outcomes/dashboard`, { params: { period } })
}
export function getAiKpi(period: 'week' | 'month' | 'quarter' = 'week') {
  return request.get<any, ApiResponse<any>>(`${U}/outcomes/ai-kpi`, { params: { period } })
}
export function getTraffic(period: 'week' | 'month' | 'quarter' = 'week') {
  return request.get<any, ApiResponse<any>>(`${U}/outcomes/traffic`, { params: { period } })
}

// agent
export function createAgentTask(data: Partial<AgentTask> & { task_type: string }) {
  return request.post<any, ApiResponse<AgentTask>>(`${A}`, data)
}
export function getAgentTask(taskId: string | number) {
  return request.get<any, ApiResponse<AgentTask>>(`${A}/${taskId}`)
}
