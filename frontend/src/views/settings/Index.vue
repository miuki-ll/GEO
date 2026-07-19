<template>
  <div>
    <div class="page-header">
      <div>
        <h2>⚙️ 系统设置</h2>
        <div class="subtitle">企业信息 / 团队成员 / 模型密钥 / 通知</div>
      </div>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="企业信息" name="profile">
        <div class="page-card" style="max-width:720px" v-loading="profileLoading">
          <el-form :model="profile" label-width="120px" label-position="right">
            <el-form-item label="企业名称"><el-input v-model="profile.name" /></el-form-item>
            <el-form-item label="行业"><el-select v-model="profile.industry"><el-option label="生美（Beauty Local）" value="beauty_local" /></el-select></el-form-item>
            <el-form-item label="License 编号"><el-input v-model="profile.license" /></el-form-item>
            <el-form-item label="联系人"><el-input v-model="profile.contact_name" /></el-form-item>
            <el-form-item label="联系电话"><el-input v-model="profile.phone" /></el-form-item>
            <el-form-item label="联系邮箱"><el-input v-model="profile.email" /></el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="save">保存修改</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="团队成员" name="members">
        <div class="page-card">
          <div style="margin-bottom:14px">
            <el-button type="primary" plain disabled>💌 邀请成员</el-button>
          </div>
          <el-table :data="members" border stripe v-loading="membersLoading">
            <el-table-column prop="name" label="成员" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="role" label="角色" width="120">
              <template #default="{ row }">
                <el-tag :type="row.role==='owner'?'danger':row.role==='admin'?'warning':'info'" size="small">{{ row.role_cn }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="join" label="加入时间" width="170" />
            <el-table-column label="操作" width="160">
              <template #default>
                <el-button link type="primary" size="small" disabled>编辑</el-button>
                <el-button link type="danger" size="small" disabled>移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="LLM 引擎配置" name="llm">
        <div class="page-card">
          <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px">
            <template #title>密钥仅保存在贵方环境变量中，系统不会上传密钥。</template>
          </el-alert>
          <el-table :data="engines" border stripe>
            <el-table-column prop="engine" label="引擎" width="140" />
            <el-table-column prop="model" label="默认模型" width="200" />
            <el-table-column prop="key" label="API Key 状态" />
            <el-table-column prop="default" label="默认使用" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.default" type="success" size="small">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default><el-button link type="primary" size="small">编辑</el-button></template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="通知与集成" name="notify">
        <div class="empty-tip">
          <el-empty description="S2 阶段实现：企业微信 / 钉钉 / 邮件通知，OSS 存储，Sentry 监控配置" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getEnterprise, updateEnterprise, listMembers } from '@/api/enterprise'
import type { EnterpriseUpdate } from '@/api/enterprise'

const tab = ref('profile')

const profileLoading = ref(false)
const saving = ref(false)
const profile = reactive({
  name: '',
  industry: 'beauty_local',
  license: '',
  contact_name: '',
  phone: '',
  email: '',
})

async function loadProfile() {
  profileLoading.value = true
  try {
    const res = await getEnterprise()
    const d = res.data as any
    if (d) {
      profile.name = d.name || ''
      profile.industry = d.industry || 'beauty_local'
      profile.license = d.license_no || ''
      profile.contact_name = d.contact_name || ''
      profile.phone = d.contact_phone || ''
      profile.email = d.contact_email || ''
    }
  } catch {
    // 加载失败保持默认
  } finally {
    profileLoading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const data: EnterpriseUpdate & { license_no?: string } = {
      name: profile.name,
      industry: profile.industry,
      license_no: profile.license,
      contact_name: profile.contact_name,
      contact_phone: profile.phone,
      contact_email: profile.email,
    }
    await updateEnterprise(data)
    ElMessage.success('已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const members = ref<any[]>([])
const membersLoading = ref(false)

const ROLE_CN: Record<string, string> = {
  owner: 'Owner',
  admin: '管理员',
  editor: '编辑',
  member: '成员',
  viewer: '只读',
}

async function loadMembers() {
  membersLoading.value = true
  try {
    const res: any = await listMembers({ page_size: 50 })
    const items = Array.isArray(res?.items)
      ? res.items
      : Array.isArray(res?.data?.items)
        ? res.data.items
        : Array.isArray(res?.data)
          ? res.data
          : []
    members.value = items.map((m: any) => ({
      ...m,
      name: m.full_name || m.name || '',
      email: m.email || '',
      role: m.role || 'member',
      role_cn: ROLE_CN[m.role] || m.role,
      join: m.created_at || '',
    }))
  } finally {
    membersLoading.value = false
  }
}

const engines = [
  { engine: '豆包', model: 'doubao-pro-32k', key: '✅ 已配置', default: false },
  { engine: 'DeepSeek', model: 'deepseek-chat', key: '✅ 已配置', default: true },
  { engine: 'Kimi', model: 'moonshot-v1-32k', key: '⚠️ 未配置', default: false },
  { engine: '文心一言', model: 'ernie-3.5', key: '⚠️ 未配置', default: false },
]

watch(tab, (v) => {
  if (v === 'profile') loadProfile()
  else if (v === 'members') loadMembers()
})

onMounted(() => {
  loadProfile()
})
</script>
