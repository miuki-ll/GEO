export interface ApiResponse<T = any> {
  code: number
  message: string
  data?: T
  total?: number
  page?: number
  page_size?: number
  items?: T[]
  request_id?: string
  errors?: string[]
}

export interface PaginationParams {
  page?: number
  page_size?: number
  keyword?: string
  sort_by?: string
  sort_order?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface UserInfo {
  id: number
  enterprise_id: number
  email: string
  phone?: string
  full_name: string
  role: 'owner' | 'admin' | 'editor' | 'member' | 'viewer'
  is_active: boolean
  avatar?: string
  last_login_at?: string
}

export interface EnterpriseProfile {
  id: number
  name: string
  industry: string
  license_no?: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  status: string
  plan: string
}

export interface KBFactItem {
  id: number
  enterprise_id: number
  title: string
  content: string
  source_type: string
  source_ref?: string
  category?: string
  tags?: string[]
  verified: boolean
  created_at: string
  updated_at: string
}

export interface KBFaqItem {
  id: number
  question: string
  answer: string
  category?: string
  fact_refs?: number[]
  verified: boolean
}

export interface ScenarioItem {
  id: number
  title: string
  user_query: string
  intent?: string
  channel: string
  skill: string
  priority: number
  status: 'draft' | 'active' | 'archived'
  target_engines?: string[]
}

export interface ContentDraftItem {
  id: number
  scenario_id: number
  title: string
  content: string
  skill: string
  channel: string
  fact_refs?: number[]
  fact_verify_pass?: boolean
  compliance_pass?: boolean
  human_review_status: 'pending' | 'approved' | 'rejected'
  status: 'draft' | 'reviewing' | 'ready' | 'published' | 'archived'
}

export interface PublishTaskItem {
  id: number
  draft_id: number
  channel: string
  mode: 'auto' | 'semi' | 'guided'
  target_url?: string
  published_url?: string
  status: 'pending' | 'running' | 'success' | 'failed'
  retry_count: number
  error_message?: string
  published_at?: string
}

export interface MonitorResultItem {
  id: number
  pool_type: 'core' | 'probe'
  engine: string
  query: string
  scenario_id?: number
  mentioned: boolean
  mention_snippet?: string
  trust_score?: number
  position_rank?: number
  run_at?: string
  batch_no?: string
}

export interface DashboardKpi {
  total_scenarios: number
  total_drafts_published: number
  avg_mention_rate: number
  avg_trust_score: number
  core_queries: number
  probe_discoveries: number
}

export interface MemberInvite {
  email: string
  full_name?: string
  role: 'owner' | 'admin' | 'editor' | 'member' | 'viewer'
}

export interface ChainStep {
  key: string
  title: string
  desc?: string
}

export interface OnboardingTaskStatus {
  status: 'idle' | 'pending' | 'running' | 'done' | 'failed'
  task_id: string
  progress_pct: number
  progress_message: string
  step?: number
}

export type OnboardingStatus = OnboardingTaskStatus
