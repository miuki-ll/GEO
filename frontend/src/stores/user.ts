import { defineStore } from 'pinia'
import type { UserInfo, LoginResult } from '@/types'
import { login as apiLogin, getCurrentUser } from '@/api/auth'
import { useAppStore } from '@/stores/app'
import { useOnboardingStore } from '@/stores/onboarding'

interface UserState {
  token: string
  user: UserInfo | null
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: '',
    user: null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    userRole: (state) => state.user?.role || 'viewer',
    enterpriseId: (state) => state.user?.enterprise_id || 0,
  },
  actions: {
    async login(email: string, password: string) {
      const res = await apiLogin({ email, password })
      if (res.data) {
        this.token = (res.data as LoginResult).access_token
        this.user = (res.data as LoginResult).user
      }
      return res
    },
    async fetchUser() {
      if (!this.token) return null
      try {
        const res = await getCurrentUser()
        this.user = (res.data as UserInfo) || null
        return this.user
      } catch {
        return null
      }
    },
    setToken(token: string) {
      this.token = token
    },
    logout() {
      this.token = ''
      this.user = null
      try {
        const appStore = useAppStore()
        appStore.$reset()
        appStore.setEnterpriseName('GEO Platform')
      } catch (e) {
        console.warn('[UserStore] app store reset skipped:', e)
      }
      try {
        const onboardingStore = useOnboardingStore()
        onboardingStore.$reset()
      } catch (e) {
        console.warn('[UserStore] onboarding store reset skipped:', e)
      }
      localStorage.removeItem('geo-user')
      localStorage.removeItem('geo-onboarding')
      sessionStorage.clear()
    },
  },
  persist: {
    key: 'geo-user',
    pick: ['token', 'user'],
  },
})
