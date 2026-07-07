import { defineStore } from 'pinia'

interface AppState {
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  loading: boolean
  enterpriseName: string
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    sidebarCollapsed: false,
    theme: 'light',
    loading: false,
    enterpriseName: 'GEO Platform',
  }),
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    setLoading(v: boolean) {
      this.loading = v
    },
    setEnterpriseName(name: string) {
      this.enterpriseName = name
    },
  },
  persist: {
    key: 'geo-app',
    pick: ['sidebarCollapsed', 'theme', 'enterpriseName'],
  },
})
