<template>
  <div>
    <div class="page-header">
      <div>
        <h2>内容草稿工作台</h2>
        <div class="subtitle">
          B3 工厂 · B4 机审/人闸门
          <!-- TODO(WAIT_FOR: A2+A3) KB/chat · TODO(WAIT_FOR: A0) 禁词以 IndustryPack 为准 -->
        </div>
      </div>
      <div>
        <el-button @click="reload">刷新列表</el-button>
        <el-button type="success" :disabled="!selected.length" @click="bulkApprove">
          批量通过 ({{ selected.length }})
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
        '数据来自数据库 content_assets。development 下若为空，后端自动种子写入。'
      "
    />

    <div class="page-card">
      <div style="display:flex; justify-content:space-between; margin-bottom:14px">
        <el-radio-group v-model="statusFilter" size="default">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="ready">ready</el-radio-button>
          <el-radio-button label="draft">draft</el-radio-button>
          <el-radio-button label="approved">approved</el-radio-button>
        </el-radio-group>
        <el-input v-model="keyword" placeholder="搜索标题" style="width: 240px" clearable />
      </div>
      <el-table :data="filtered" border stripe @selection-change="onSelect">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="channel" label="渠道" width="100" />
        <el-table-column label="机审" min-width="200">
          <template #default="{ row }">
            <el-tooltip
              content="绿=该项通过；禁词绿=未命中禁词（五键同向 true=通过）"
              placement="top"
            >
              <span>
                <span
                  class="mr-tag"
                  v-for="(ok, key) in row.machine_review || {}"
                  :key="key"
                  :class="ok ? 'ok' : 'bad'"
                >
                  {{ shortKey(String(key)) }}
                </span>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="切片" width="70">
          <template #default="{ row }">{{ (row.rag_slices || []).length }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="preview(row)">预览</el-button>
            <el-button link type="warning" size="small" @click="doReview(row)">机审</el-button>
            <el-button link type="success" size="small" @click="doApprove(row)">通过</el-button>
            <el-button link type="danger" size="small" @click="doReject(row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="!filtered.length" class="empty">暂无草稿 — 可先在方案包确认 scenario 触发生成</p>
    </div>

    <el-drawer v-model="drawer" title="草稿预览（7 段式 / RAG / 机审）" size="48%">
      <template v-if="current">
        <p><b>status:</b> {{ current.status }}</p>
        <p><b>fact_refs:</b> {{ (current.fact_refs || []).join(', ') }}</p>
        <p><b>machine_review:</b> {{ JSON.stringify(current.machine_review || {}) }}</p>
        <p><b>rag_slices:</b> {{ (current.rag_slices || []).length }} 块</p>

        <el-divider content-position="left">7 段式正文</el-divider>
        <div class="md-body" v-html="renderSimpleMarkdown(current.body || current.content || '')" />

        <el-divider content-position="left">RAG 切片</el-divider>
        <el-empty
          v-if="!(current.rag_slices || []).length"
          description="暂无切片（旧草稿可能未写入 metadata；可重新确认方案包生成）"
        />
        <div v-for="(sl, idx) in current.rag_slices || []" :key="idx" class="slice-card">
          <h4 class="slice-title">
            {{ idx + 1 }}. {{ stripHeadingMarks(sl.title) || '未命名切片' }}
            <span class="muted">（{{ sl.chars ?? (sl.body || '').length }} 字）</span>
          </h4>
          <div class="slice-meta">
            <div class="meta-row">
              <b>摘要</b>
              <div class="md-inline" v-html="renderSimpleMarkdown(sl.summary || '—')" />
            </div>
            <div class="meta-row">
              <b>关键词</b>
              <span class="muted">{{ (sl.keywords || []).join(' · ') || '—' }}</span>
            </div>
          </div>
          <div class="md-body slice-md" v-html="renderSimpleMarkdown(sl.body || '')" />
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listDrafts,
  getDraft,
  bulkApproveDrafts,
  approveDraft,
  rejectDraft,
  runMachineReview,
} from '@/api/ops'
import { renderSimpleMarkdown } from '@/utils/simpleMarkdown'

const router = useRouter()
const statusFilter = ref('all')
const keyword = ref('')
const selected = ref<any[]>([])
const loadError = ref('')
const drafts = ref<any[]>([])
const drawer = ref(false)
const current = ref<any>(null)

function shortKey(k: string) {
  const map: Record<string, string> = {
    fact_verify: '事实',
    forbidden_words: '禁词',
    cross_validation: '交叉',
    entity_consistency: '实体',
    rag_readability: 'RAG',
  }
  return map[k] || k.slice(0, 2)
}

function stripHeadingMarks(title?: string) {
  return String(title || '')
    .replace(/^#+\s*/, '')
    .trim()
}

const filtered = computed(() => {
  let rows = drafts.value
  if (statusFilter.value !== 'all') {
    rows = rows.filter((d) => d.status === statusFilter.value)
  }
  if (keyword.value.trim()) {
    const q = keyword.value.trim()
    rows = rows.filter((d) => String(d.title).includes(q))
  }
  return rows
})

function onSelect(rows: any[]) {
  selected.value = rows
}

async function preview(row: any) {
  current.value = row
  drawer.value = true
  if (!(row.rag_slices || []).length && row.id) {
    try {
      const res: any = await getDraft(row.id)
      const detail = res?.data || res
      if (detail) {
        current.value = { ...row, ...detail }
        Object.assign(row, detail)
      }
    } catch {
      /* keep list row */
    }
  }
}

async function reload() {
  loadError.value = ''
  try {
    const res: any = await listDrafts({ page: 1, page_size: 50 })
    const data = res?.data
    const items = Array.isArray(data) ? data : data?.items || []
    drafts.value = items
    if (items.length) {
      ElMessage.success(`已从数据库加载 ${items.length} 条草稿`)
    } else {
      ElMessage.info('数据库暂无草稿（可先确认方案包，或等种子写入）')
    }
  } catch (e: any) {
    drafts.value = []
    loadError.value = e?.message || '草稿 API 失败（请确认后端与 MySQL）'
    ElMessage.error(loadError.value)
  }
}

async function doReview(row: any) {
  try {
    const res: any = await runMachineReview(row.id)
    ElMessage.success('机审完成')
    Object.assign(row, res?.data || {})
  } catch {
    ElMessage.warning('机审 API 失败（可用 MOCK 预览）')
  }
}

async function doApprove(row: any) {
  try {
    await approveDraft(row.id)
    ElMessage.success('已通过')
    reload()
  } catch {
    ElMessage.warning('通过失败')
  }
}

async function doReject(row: any) {
  try {
    const { value } = await ElMessageBox.prompt('驳回原因', '人闸门驳回', {
      inputPlaceholder: '例如：价格需更新',
    })
    const res: any = await rejectDraft(row.id, value)
    ElMessage.success(`已驳回 → ${res?.data?.status || 'draft'}`)
    reload()
  } catch {
    /* cancel */
  }
}

function bulkApprove() {
  ElMessageBox.confirm(`确认批量通过 ${selected.value.length} 篇？`, '人闸门', { type: 'warning' })
    .then(async () => {
      const ids = selected.value.map((r) => r.id).filter(Boolean)
      try {
        const res: any = await bulkApproveDrafts(ids)
        const next = res?.data?.next_route || '/publish/tasks'
        ElMessage.success(`已通过 ${res?.data?.approved ?? ids.length} 条`)
        router.push(next)
      } catch {
        ElMessage.warning('批量通过失败')
      }
    })
    .catch(() => {})
}

onMounted(reload)
</script>

<style scoped>
.empty {
  text-align: center;
  color: #909399;
  padding: 24px;
}
.body-pre {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.5;
  background: #f7f8fa;
  padding: 12px;
  border-radius: 8px;
}
.md-body {
  font-size: 14px;
  line-height: 1.7;
  color: #303133;
  background: #f7f8fa;
  padding: 14px 16px;
  border-radius: 8px;
}
.md-body :deep(.md-h) {
  margin: 14px 0 8px;
  font-weight: 700;
  color: #1f2a44;
  line-height: 1.35;
}
.md-body :deep(.md-h1) {
  font-size: 18px;
}
.md-body :deep(.md-h2),
.md-body :deep(.md-h3) {
  font-size: 16px;
}
.md-body :deep(.md-h:first-child) {
  margin-top: 0;
}
.md-body :deep(.md-p) {
  margin: 0 0 8px;
}
.md-body :deep(.md-ol),
.md-body :deep(.md-ul) {
  margin: 0 0 10px;
  padding-left: 1.4em;
}
.md-body :deep(.md-ol li),
.md-body :deep(.md-ul li) {
  margin: 4px 0;
}
.md-body :deep(.md-fact) {
  display: inline-block;
  font-weight: 600;
  color: #409eff;
  margin-right: 4px;
}
.md-inline :deep(.md-h),
.md-inline :deep(.md-p) {
  display: inline;
  margin: 0;
  font-size: 12px;
  font-weight: 400;
  color: #606266;
}
.md-inline :deep(.md-h) {
  font-weight: 600;
  color: #303133;
}
.slice-card {
  margin-bottom: 14px;
  padding: 12px 14px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}
.slice-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: #1f2a44;
}
.slice-meta {
  margin-bottom: 10px;
}
.meta-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin: 4px 0;
  font-size: 12px;
}
.meta-row > b {
  flex: 0 0 48px;
  color: #606266;
}
.slice-md {
  background: #f7f8fa;
  padding: 10px 12px;
}
.muted {
  color: #909399;
  font-size: 12px;
  margin: 4px 0;
}
.mr-tag {
  display: inline-block;
  margin: 0 2px 2px 0;
  padding: 0 4px;
  font-size: 11px;
  border-radius: 3px;
}
.mr-tag.ok {
  background: #e8f8ef;
  color: #1a7f4b;
}
.mr-tag.bad {
  background: #fdecec;
  color: #c45656;
}
</style>
