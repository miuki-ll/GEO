import request from '@/utils/request'
import type {
  ApiResponse,
  PaginationParams,
  EnterpriseProfile,
  UserInfo,
  MemberInvite,
} from '@/types/index'

export interface EnterpriseUpdate {
  name?: string
  industry?: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  settings?: Record<string, any>
}

export function getEnterprise() {
  return request.get<any, ApiResponse<EnterpriseProfile>>('/api/v1/user/enterprise/profile')
}

export function updateEnterprise(data: EnterpriseUpdate) {
  return request.put<any, ApiResponse<EnterpriseProfile>>('/api/v1/user/enterprise/profile', data)
}

export function listMembers(params: PaginationParams & { role?: string; status?: string } = {}) {
  return request.get<any, ApiResponse<UserInfo[]>>('/api/v1/user/enterprise/members', { params })
}

export function inviteMember(data: MemberInvite) {
  return request.post<any, ApiResponse<UserInfo>>('/api/v1/user/enterprise/members/invite', data)
}

export function updateMember(memberId: number, data: Partial<UserInfo> & { is_active?: boolean; role?: string }) {
  return request.patch<any, ApiResponse<UserInfo>>(`/api/v1/user/enterprise/members/${memberId}`, data)
}

