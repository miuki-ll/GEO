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
        <div class="page-card" style="max-width:720px">
          <el-form :model="profile" label-width="120px" label-position="right">
            <el-form-item label="企业名称"><el-input v-model="profile.name" /></el-form-item>
            <el-form-item label="行业"><el-select v-model="profile.industry"><el-option label="生美（Beauty Local）" value="beauty_local" /></el-select></el-form-item>
            <el-form-item label="License 编号"><el-input v-model="profile.license" /></el-form-item>
            <el-form-item label="联系人"><el-input v-model="profile.contact_name" /></el-form-item>
            <el-form-item label="联系电话"><el-input v-model="profile.phone" /></el-form-item>
            <el-form-item label="联系邮箱"><el-input v-model="profile.email" /></el-form-item>
            <el-form-item>
              <el-button type="primary" @click="save">保存修改</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="团队成员" name="members">
        <div class="page-card">
          <div style="margin-bottom:14px">
            <el-button type="primary" plain>💌 邀请成员</el-button>
          </div>
          <el-table :data="members" border stripe>
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
                <el-button link type="primary" size="small">编辑</el-button>
                <el-button link type="danger" size="small">移除</el-button>
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
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
const tab = ref('profile')
const profile = reactive({
  name: 'XX 皮肤管理中心',
  industry: 'beauty_local',
  license: 'MEEXXXXXX',
  contact_name: 'Demo User',
  phone: '138****8888',
  email: 'demo@geo.test',
})
const members = [
  { name: 'Demo User', email: 'demo@geo.test', role: 'owner', role_cn: 'Owner', join: '2026-07-01 10:00' },
  { name: '运营小姐姐', email: 'ops@geo.test', role: 'admin', role_cn: '管理员', join: '2026-07-03 14:20' },
  { name: '内容编辑', email: 'editor@geo.test', role: 'editor', role_cn: '编辑', join: '2026-07-04 09:10' },
]
const engines = [
  { engine: '豆包', model: 'doubao-pro-32k', key: '✅ 已配置', default: false },
  { engine: 'DeepSeek', model: 'deepseek-chat', key: '✅ 已配置', default: true },
  { engine: 'Kimi', model: 'moonshot-v1-32k', key: '⚠️ 未配置', default: false },
  { engine: '文心一言', model: 'ernie-3.5', key: '⚠️ 未配置', default: false },
]
function save() {
  ElMessage.success('已保存（S2 阶段真实写入企业资料）')
}
</script>

