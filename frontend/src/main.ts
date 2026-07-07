import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElNotification, ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

import App from './App.vue'
import router from './router'
import './assets/style/global.scss'

NProgress.configure({ showSpinner: false })

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component as any)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.config.errorHandler = (err, _vm, info) => {
  const msg = err instanceof Error ? err.message : String(err)
  console.error('[GEO Vue Error] info=%s msg=%s err=%o', info, msg, err)
  ElNotification({
    type: 'error',
    title: '系统异常',
    message: msg || '页面发生错误，已自动恢复。如反复出现请联系客服',
    duration: 4500,
    showClose: true,
  })
}

window.addEventListener('error', (ev: ErrorEvent) => {
  console.error('[GEO Window Error]', ev.message, ev.filename, ev.lineno, ev.colno, ev.error)
  return true
})

window.addEventListener('unhandledrejection', (ev: PromiseRejectionEvent) => {
  const reason = ev.reason
  const msg = reason instanceof Error ? reason.message : typeof reason === 'string' ? reason : '异步操作失败，请稍后重试'
  console.error('[GEO Unhandled Promise]', reason)
  if (msg && !/Unauthorized|Forbidden|cancel/i.test(msg)) {
    ElMessage.warning(msg)
  }
  ev.preventDefault()
})

app.mount('#app')

