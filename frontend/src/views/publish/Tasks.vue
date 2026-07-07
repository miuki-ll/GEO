<template>
  <div>
    <div class="page-header">
      <div>
        <h2>🚀 发布引擎</h2>
        <div class="subtitle">托管页 AUTO · 小红书/知乎 SEMI · 点评 GUIDED</div>
      </div>
      <el-button type="primary">+ 新建发布</el-button>
    </div>

    <div class="stat-grid" style="margin-bottom: 16px">
      <div class="kpi-card"><div class="accent-bar"></div><div class="label">今日发布</div><div class="value">7</div></div>
      <div class="kpi-card"><div class="accent-bar" style="background:#67c23a"></div><div class="label">成功</div><div class="value">5</div></div>
      <div class="kpi-card"><div class="accent-bar" style="background:#f56c6c"></div><div class="label">失败 (AUTO→SEMI)</div><div class="value">2</div></div>
      <div class="kpi-card"><div class="accent-bar" style="background:#e6a23c"></div><div class="label">等待人工</div><div class="value">3</div></div>
    </div>

    <div class="page-card">
      <el-table :data="tasks" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="draft" label="草稿标题" min-width="240" />
        <el-table-column prop="channel" label="渠道" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.mode==='auto'?'success':row.mode==='semi'?'warning':'info'">{{ row.channel }} · {{ row.mode.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status_cn }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="retry" label="重试" width="70" align="center" />
        <el-table-column prop="published_at" label="发布时间" width="170" />
        <el-table-column prop="url" label="已发布链接" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <a v-if="row.url" :href="row.url" target="_blank" rel="noopener">{{ row.url }}</a>
            <span v-else style="color:#909399">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status==='failed'" link type="warning" size="small" @click="doRetry(row)">切 SEMI 重试</el-button>
            <el-button v-if="row.status==='running'" link size="small">查看日志</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
const tasks = [
  { id: 101, draft: 'FAQ：敏感肌能做美容院项目吗？', channel: '托管页', mode: 'auto', status: 'success', status_cn: '成功', retry: 0, published_at: '2026-07-05 10:12', url: 'https://hosted.example.com/faq/1' },
  { id: 102, draft: '【敏感肌必看】XX 美容院补水修护全流程', channel: '小红书', mode: 'auto', status: 'failed', status_cn: '失败', retry: 2, published_at: '—', url: '' },
  { id: 103, draft: '2026 夏天油皮怎么选美容院项目', channel: '知乎', mode: 'semi', status: 'pending', status_cn: '待人工', retry: 0, published_at: '—', url: '' },
  { id: 104, draft: '门店决策卡', channel: '托管页', mode: 'auto', status: 'running', status_cn: '发布中', retry: 0, published_at: '—', url: '' },
]
function statusType(s: string) {
  return { success: 'success', failed: 'danger', pending: 'warning', running: '' }[s] || 'info'
}
function doRetry(row: any) {
  ElMessageBox.confirm(`AUTO 失败，切换到 SEMI 模式（需人工扫码）重新发布 ${row.draft}？`, '降级发布', { type: 'warning' })
    .then(() => ElMessage.success('已创建 SEMI 任务'))
    .catch(() => {})
}
</script>

