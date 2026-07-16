<template>
  <div>
    <div class="page-header">
      <div>
        <h2>内容草稿工作台</h2>
        <div class="subtitle">
          草稿列表 · 机审标示 · 人闸门（B0 骨架）
          <!-- TODO(WAIT_FOR: A-fixture) / TODO(WAIT_FOR: B3) 真 drafts API -->
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
      type="info"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      :title="usingMock ? 'MOCK 草稿列表（B0）。真接 content API 后替换。' : '已加载 API 草稿'"
    />

    <div class="page-card">
      <div style="display:flex; justify-content:space-between; margin-bottom:14px">
        <el-radio-group v-model="statusFilter" size="default">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="ready">待审 ready</el-radio-button>
          <el-radio-button label="draft">draft</el-radio-button>
        </el-radio-group>
        <el-input v-model="keyword" placeholder="搜索标题" style="width: 240px" clearable />
      </div>
      <el-table :data="filtered" border stripe @selection-change="selected = $event">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="240" />
        <el-table-column prop="channel" label="渠道" width="110" />
        <el-table-column prop="skill" label="Skill" width="100" />
        <el-table-column label="fact_refs" width="120">
          <template #default="{ row }">{{ (row.fact_refs || []).join(',') }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default>
            <el-button link type="primary" size="small">预览</el-button>
            <el-button link type="success" size="small">通过</el-button>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="!filtered.length" class="empty">暂无草稿（列表区已就绪，等待 B3 生成）</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import handoffMock from '@/mocks/handoff_a_to_b.json'

const statusFilter = ref('all')
const keyword = ref('')
const selected = ref<any[]>([])
const usingMock = ref(true)
const drafts = ref<any[]>([])

function buildMockDrafts() {
  const facts = (handoffMock.kb_facts || []).map((f: any) => f.id)
  return [
    {
      id: 1,
      title: '敏感肌能不能做皮肤管理？',
      channel: 'hosted',
      skill: 'faq',
      fact_refs: facts.slice(0, 3),
      status: 'ready',
    },
    {
      id: 2,
      title: '静安寺附近做脸哪家不推销（笔记体）',
      channel: 'xiaohongshu',
      skill: 'article',
      fact_refs: facts.slice(0, 2),
      status: 'ready',
    },
  ]
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

function reload() {
  // TODO(WAIT_FOR: B3) GET /content/drafts
  drafts.value = buildMockDrafts()
  usingMock.value = true
  ElMessage.success('已刷新 MOCK 草稿列表')
}

function bulkApprove() {
  ElMessageBox.confirm(`确认批量通过 ${selected.value.length} 篇？`, '人闸门', { type: 'warning' })
    .then(() => ElMessage.success('MOCK：已记录通过（B4 接 approval_log）'))
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
</style>
