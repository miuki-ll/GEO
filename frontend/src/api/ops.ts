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

// content
export function listDrafts(params: PaginationParams & { status?: string; channel?: string } = {}) {
  return request.get<any, ApiResponse<ContentDraftItem[]>>('/api/v1/content/drafts', { params })
}
export function createDraft(data: Partial<ContentDraftItem>) {
  return request.post<any, ApiResponse<ContentDraftItem>>('/api/v1/content/drafts', data)
}
export function updateDraft(id: number, data: Partial<ContentDraftItem>) {
  return request.put<any, ApiResponse<ContentDraftItem>>(`/api/v1/content/drafts/${id}`, data)
}
export function bulkApproveDrafts(ids: number[]) {
  return request.post<any, ApiResponse<any>>('/api/v1/content/bulk-approve', { ids })
}
export function triggerContentProduce(data: ProduceRequest = {}) {
  return request.post<any, ApiResponse<AgentTask>>('/api/v1/agent/tasks', {
    task_type: 'content_produce',
    graph_name: 'content_pipeline',
    input_data: data,
  })
}

// publish
export function listPublishTasks(params: PaginationParams & { status?: string; channel?: string } = {}) {
  return request.get<any, ApiResponse<PublishTaskItem[]>>('/api/v1/publish/tasks', { params })
}
export function createPublishTask(data: Partial<PublishTaskItem> & { draft_id: number }) {
  return request.post<any, ApiResponse<PublishTaskItem>>('/api/v1/publish/tasks', data)
}
export function retryPublishTask(taskId: number) {
  return request.post<any, ApiResponse<PublishTaskItem>>(`/api/v1/publish/tasks/${taskId}/retry`)
}
export function semiPublish(data: { draft_id: number; manual_meta?: any }) {
  return request.post<any, ApiResponse<PublishTaskItem>>('/api/v1/publish/semi', data)
}

// monitor
export function listCore(params: PaginationParams = {}) {
  return request.get<any, ApiResponse<MonitorResultItem[]>>('/api/v1/monitor/core', { params })
}
export function listProbe(params: PaginationParams = {}) {
  return request.get<any, ApiResponse<MonitorResultItem[]>>('/api/v1/monitor/probe', { params })
}
export function triggerMonitor(pool: 'core' | 'probe') {
  return request.post<any, ApiResponse<AgentTask>>('/api/v1/monitor/trigger', { pool })
}

// outcomes
export function getDashboard(period: 'week' | 'month' | 'quarter' = 'week') {
  return request.get<any, ApiResponse<DashboardKpi>>('/api/v1/outcomes/dashboard', { params: { period } })
}
export function getAiKpi(period: 'week' | 'month' | 'quarter' = 'week') {
  return request.get<any, ApiResponse<any>>('/api/v1/outcomes/ai-kpi', { params: { period } })
}
export function getTraffic(period: 'week' | 'month' | 'quarter' = 'week') {
  return request.get<any, ApiResponse<any>>('/api/v1/outcomes/traffic', { params: { period } })
}

// agent
export function createAgentTask(data: Partial<AgentTask> & { task_type: string }) {
  return request.post<any, ApiResponse<AgentTask>>('/api/v1/agent/tasks', data)
}
export function getAgentTask(taskId: string) {
  return request.get<any, ApiResponse<AgentTask>>(`/api/v1/agent/${taskId}`)
}
