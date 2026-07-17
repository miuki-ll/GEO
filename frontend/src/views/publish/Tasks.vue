<template>
  <div>
    <div class="page-header">
      <div>
        <h2>发布引擎</h2>
        <div class="subtitle">
          托管页 AUTO（MOCK）· 小红书/知乎 SEMI 导出包 · GUIDED
          <!-- TODO(WAIT_FOR: A5) 托管页真发 -->
        </div>
      </div>
      <div>
        <el-button @click="reload">刷新</el-button>
        <el-button type="primary" :disabled="!selected.length" @click="runSelected">
          批量 Run ({{ selected.length }})
        </el-button>
      </div>
    </div>

    <el-alert
      :type="loadError ? 'error' : 'info'"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      :title="
        loadError ||
        '数据来自 publish_tasks。人审通过后自动建任务；development 下会对 ready/approved 草稿补齐。'
      "
    />

    <div class="stat-grid" style="margin-bottom: 16px">
      <div class="kpi-card">
        <div class="accent-bar"></div>
        <div class="label">全部</div>
        <div class="value">{{ tasks.length }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#67c23a"></div>
        <div class="label">已发布</div>
        <div class="value">{{ countBy('published') }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#e6a23c"></div>
        <div class="label">待处理</div>
        <div class="value">{{ countBy('pending') }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#f56c6c"></div>
        <div class="label">失败</div>
        <div class="value">{{ countBy('failed') }}</div>
      </div>
    </div>

    <div class="page-card">
      <el-table :data="tasks" border stripe v-loading="loading" @selection-change="onSelect">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="草稿标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="channel" label="渠道" width="140">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.mode === 'auto' ? 'success' : row.mode === 'semi' ? 'warning' : 'info'"
            >
              {{ row.channel }} · {{ String(row.mode || '').toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusCn(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="retry_count" label="重试" width="70" align="center" />
        <el-table-column prop="published_at" label="发布时间" width="170" />
        <el-table-column prop="published_url" label="已发布链接" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <a v-if="row.published_url" :href="row.published_url" target="_blank" rel="noopener">
              {{ row.published_url }}
            </a>
            <span v-else style="color:#909399">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.mode === 'auto' && row.status === 'pending'"
              link
              type="success"
              size="small"
              @click="doAuto(row)"
            >
              AUTO 发布
            </el-button>
            <el-button
              v-if="row.mode === 'semi'"
              link
              type="primary"
              size="small"
              @click="showExport(row)"
            >
              导出包
            </el-button>
            <el-button
              v-if="row.mode === 'semi' && row.status === 'pending'"
              link
              type="warning"
              size="small"
              @click="doSemi(row)"
            >
              回填外链
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="!tasks.length && !loading" class="empty">暂无发布任务 — 请先在草稿页人审通过</p>
    </div>

    <el-drawer v-model="exportOpen" title="SEMI 导出包" size="42%">
      <template v-if="exportPkg">
        <p><b>title</b></p>
        <p>{{ exportPkg.title }}</p>
        <p><b>tags</b></p>
        <p>{{ (exportPkg.tags || []).join(' · ') }}</p>
        <p><b>cover_hint</b></p>
        <p>{{ exportPkg.cover_hint }}</p>
        <p><b>steps</b></p>
        <ol>
          <li v-for="(s, i) in exportPkg.steps || []" :key="i">{{ s }}</li>
        </ol>
        <p><b>body</b></p>
        <pre class="body-pre">{{ exportPkg.body }}</pre>
        <el-button type="primary" @click="copyBody">复制正文</el-button>
      </template>
      <el-empty v-else description="无 export_package（可点批量 Run 生成）" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listPublishTasks,
  runPublish,
  autoPublish,
  semiPublish,
} from '@/api/ops'

const loading = ref(false)
const loadError = ref('')
const tasks = ref<any[]>([])
const selected = ref<any[]>([])
const exportOpen = ref(false)
const exportPkg = ref<any>(null)

function countBy(status: string) {
  return tasks.value.filter((t) => t.status === status).length
}

function statusType(s: string) {
  return (
    ({ published: 'success', failed: 'danger', pending: 'warning', running: '' } as Record<string, string>)[
      s
    ] || 'info'
  )
}

function statusCn(s: string) {
  return (
    ({ published: '已发布', failed: '失败', pending: '待处理', running: '发布中' } as Record<string, string>)[
      s
    ] || s
  )
}

function onSelect(rows: any[]) {
  selected.value = rows
}

async function reload() {
  loading.value = true
  loadError.value = ''
  try {
    const res: any = await listPublishTasks({ page: 1, page_size: 50 })
    const data = res?.data
    const items = Array.isArray(data) ? data : data?.items || []
    tasks.value = items
    if (items.length) ElMessage.success(`已加载 ${items.length} 条发布任务`)
    else ElMessage.info('暂无发布任务')
  } catch (e: any) {
    tasks.value = []
    loadError.value = e?.message || '发布 API 失败（请确认后端与 MySQL）'
    ElMessage.error(loadError.value)
  } finally {
    loading.value = false
  }
}

async function runSelected() {
  try {
    const ids = selected.value.map((t) => t.id)
    const res: any = await runPublish(ids)
    ElMessage.success(`已启动 ${res?.data?.started ?? ids.length} 个任务`)
    await reload()
  } catch (e: any) {
    ElMessage.error(e?.message || '批量 Run 失败')
  }
}

async function doAuto(row: any) {
  try {
    await autoPublish(row.id)
    ElMessage.success('AUTO MOCK 发布完成')
    await reload()
  } catch (e: any) {
    ElMessage.error(e?.message || 'AUTO 失败')
  }
}

function showExport(row: any) {
  exportPkg.value = row.export_package || null
  exportOpen.value = true
  if (!exportPkg.value) {
    ElMessage.info('暂无导出包，可先点「批量 Run」生成')
  }
}

async function doSemi(row: any) {
  try {
    const { value } = await ElMessageBox.prompt('粘贴已发布外链 URL', 'SEMI 回填', {
      inputPlaceholder: 'https://...',
      confirmButtonText: '标记已发布',
    })
    if (!value?.trim()) return
    await semiPublish(row.id, value.trim())
    ElMessage.success('已标记发布')
    await reload()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || '回填失败')
  }
}

async function copyBody() {
  const text = exportPkg.value?.body || ''
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('正文已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择正文')
  }
}

onMounted(reload)
</script>

<style scoped>
.empty {
  color: #909399;
  padding: 16px 0 0;
  margin: 0;
}
.body-pre {
  white-space: pre-wrap;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  max-height: 360px;
  overflow: auto;
  font-size: 13px;
}
</style>
