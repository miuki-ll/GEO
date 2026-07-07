import axios, { AxiosInstance, AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import NProgress from 'nprogress'
import { useUserStore } from '@/stores/user'
import type { ApiResponse } from '@/types'

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    NProgress.start()
    const userStore = useUserStore()
    if (userStore.token && config.headers) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error: AxiosError) => {
    NProgress.done()
    return Promise.reject(error)
  },
)

request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    NProgress.done()
    const res = response.data
    if (res.code === 0 || res.code === undefined) {
      return res as any
    }
    if (res.code === 401) {
      const userStore = useUserStore()
      userStore.logout()
      ElMessageBox.confirm('登录状态已过期，请重新登录', '提示', {
        confirmButtonText: '重新登录',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(() => {
          window.location.href = '/login'
        })
        .catch(() => {})
      return Promise.reject(new Error(res.message || 'Unauthorized'))
    }
    if (res.code === 403) {
      ElMessage.error('权限不足')
      return Promise.reject(new Error('Forbidden'))
    }
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || 'Error'))
  },
  (error: AxiosError) => {
    NProgress.done()
    const status = error.response?.status
    const errData = error.response?.data as ApiResponse | undefined
    const msg =
      errData?.message ||
      (error as any).message ||
      (status === 500 ? '服务器内部错误' : '网络错误，请稍后再试')
    if (status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      const path = window.location.pathname
      if (path !== '/login' && path !== '/register') {
        ElMessageBox.confirm('登录状态已过期，请重新登录', '提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning',
        })
          .then(() => {
            window.location.href = '/login'
          })
          .catch(() => {})
      }
      return Promise.reject(new Error(errData?.message || 'Unauthorized'))
    }
    if (status === 403) {
      ElMessage.error('权限不足')
      return Promise.reject(new Error('Forbidden'))
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default request
