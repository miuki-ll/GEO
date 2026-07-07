import request from '@/utils/request'
import type { ApiResponse, LoginPayload, LoginResult, UserInfo } from '@/types'

export function login(data: LoginPayload) {
  return request.post<any, ApiResponse<LoginResult>>('/api/v1/auth/login', data)
}

export function register(data: any) {
  return request.post<any, ApiResponse>('/api/v1/auth/register', data)
}

export function getCurrentUser() {
  return request.get<any, ApiResponse<UserInfo>>('/api/v1/auth/me')
}
