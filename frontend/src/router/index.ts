import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    redirect: '/outcomes',
    children: [
      {
        path: 'onboarding',
        name: 'Onboarding',
        component: () => import('@/views/onboarding/Index.vue'),
        meta: { title: '开店向导' },
      },
      {
        path: 'strategy-pack',
        name: 'StrategyPack',
        component: () => import('@/views/strategy/Index.vue'),
        meta: { title: '方案包' },
      },
      {
        path: 'outcomes',
        name: 'Outcomes',
        component: () => import('@/views/outcomes/Index.vue'),
        meta: { title: '效果舱' },
      },
      {
        path: 'knowledge-base',
        name: 'KnowledgeBase',
        component: () => import('@/views/knowledge-base/Index.vue'),
        meta: { title: '知识库' },
      },
      {
        path: 'content/drafts',
        name: 'ContentDrafts',
        component: () => import('@/views/content/Drafts.vue'),
        meta: { title: '内容草稿' },
      },
      {
        path: 'publish/tasks',
        name: 'PublishTasks',
        component: () => import('@/views/publish/Tasks.vue'),
        meta: { title: '发布任务' },
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/monitor/Index.vue'),
        meta: { title: 'AI 监测' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Index.vue'),
        meta: { title: '系统设置' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404', public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to, _from, next) => {
  NProgress.start()
  const titleSuffix = import.meta.env.VITE_APP_TITLE
  document.title = to.meta?.title ? `${to.meta.title} · ${titleSuffix}` : titleSuffix
  const userStore = useUserStore()

  if (to.meta?.public) {
    if ((to.name === 'Login' || to.name === 'Register') && userStore.isLoggedIn) {
      return next('/outcomes')
    }
    return next()
  }

  if (!userStore.isLoggedIn) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  if (!userStore.user) {
    try {
      await userStore.fetchUser()
    } catch {
      userStore.logout()
      return next({ name: 'Login' })
    }
  }
  next()
})

router.afterEach(() => {
  NProgress.done()
})

router.onError((err, to, _from) => {
  const msg = err instanceof Error ? err.message : String(err)
  console.error('[GEO Router Error] to=%s msg=%s err=%o', to?.fullPath, msg, err)
  if (/ChunkLoadError|Loading chunk .* failed|Failed to fetch dynamically imported module/i.test(msg || '')) {
    NProgress.done()
    ElMessage.warning('检测到页面资源版本过期，正在刷新更新资源...')
    setTimeout(() => {
      window.location.reload()
    }, 600)
  }
})

export default router
