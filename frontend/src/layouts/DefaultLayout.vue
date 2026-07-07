<template>
  <el-container class="default-layout" v-loading="appStore.loading">
    <el-aside :width="appStore.sidebarCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo-wrap">
        <img src="/favicon.svg" alt="logo" class="logo-img" />
        <span v-if="!appStore.sidebarCollapsed" class="logo-text">GEO 运营台</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        :collapse="appStore.sidebarCollapsed"
        class="side-menu"
        background-color="transparent"
        text-color="#cfd3dc"
        active-text-color="#409eff"
      >
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <template #title>{{ m.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <el-button text @click="appStore.toggleSidebar()">
            <el-icon><Fold v-if="!appStore.sidebarCollapsed" /><Expand v-else /></el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ appStore.enterpriseName }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ $route.meta?.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="topbar-right">
          <el-dropdown trigger="click" @command="onUserCmd">
            <span class="user-info">
              <el-avatar :size="32">{{ userStore.user?.full_name?.[0] || 'U' }}</el-avatar>
              <span class="user-name">{{ userStore.user?.full_name || '未登录' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  MagicStick,
  Files,
  DataAnalysis,
  Reading,
  Document,
  UploadFilled,
  Monitor,
  Setting,
  Fold,
  Expand,
  ArrowDown,
} from '@element-plus/icons-vue'
import { useAppStore, useUserStore } from '@/stores'

const appStore = useAppStore()
const userStore = useUserStore()
const router = useRouter()

const menus = computed(() => [
  { path: '/onboarding', title: '开店向导', icon: MagicStick },
  { path: '/strategy-pack', title: '方案包', icon: Files },
  { path: '/outcomes', title: '效果舱', icon: DataAnalysis },
  { path: '/knowledge-base', title: '知识库', icon: Reading },
  { path: '/content/drafts', title: '内容草稿', icon: Document },
  { path: '/publish/tasks', title: '发布任务', icon: UploadFilled },
  { path: '/monitor', title: 'AI 监测', icon: Monitor },
  { path: '/settings', title: '设置', icon: Setting },
])

function onUserCmd(cmd: string) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
      .then(() => {
        userStore.logout()
        router.push('/login')
      })
      .catch(() => {})
  } else if (cmd === 'settings') {
    router.push('/settings')
  } else if (cmd === 'profile') {
    router.push('/settings')
  }
}
</script>

<style lang="scss" scoped>
.default-layout {
  height: 100vh;
  background: #f5f7fa;
}
.sidebar {
  background: linear-gradient(180deg, #1f2a44 0%, #182037 100%);
  color: #fff;
  transition: width 0.25s ease;
  overflow: hidden;
}
.logo-wrap {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.logo-img {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  flex-shrink: 0;
}
.logo-text {
  color: #fff;
  font-weight: 600;
  font-size: 16px;
  white-space: nowrap;
}
.side-menu {
  border-right: none;
  padding-top: 8px;
}
.topbar {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.user-info {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
  &:hover {
    background: #f0f2f5;
  }
}
.user-name {
  font-size: 14px;
  color: #303133;
}
.main-content {
  padding: 20px;
  overflow-y: auto;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
