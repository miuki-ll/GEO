<template>
  <div>
    <div class="page-header">
      <div>
        <h2>📝 内容草稿工作台</h2>
        <div class="subtitle">Scenario → Skill → Content · 机器审 + 人工审双闸门</div>
      </div>
      <div>
        <el-button @click="runProduce">🔬 触发生产 Agent</el-button>
        <el-button type="success" :disabled="!selected.length" @click="bulkApprove">✅ 批量通过 ({{ selected.length }})</el-button>
      </div>
    </div>

    <div class="page-card">
      <div style="display:flex; justify-content:space-between; margin-bottom:14px">
        <el-filter-panel>
          <el-radio-group v-model="status" size="default">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="pending">待审核</el-radio-button>
            <el-radio-button label="approved">已通过</el-radio-button>
            <el-radio-button label="rejected">已驳回</el-radio-button>
          </el-radio-group>
        </el-filter-panel>
        <el-input placeholder="搜索标题" style="width: 240px" clearable />
      </div>
      <el-table :data="drafts" border stripe @selection-change="selected = $event">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" min-width="240" />
        <el-table-column prop="channel" label="渠道" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="tagType(row.channel)">{{ row.channel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="skill" label="Skill" width="100" />
        <el-table-column prop="fact_ok" label="Fact校验" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.fact_ok" size="small" type="success">通过</el-tag>
            <el-tag v-else size="small" type="danger">未通过</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="compliance_ok" label="合规校验" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.compliance_ok" size="small" type="success">通过</el-tag>
            <el-tag v-else size="small" type="danger">未通过</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="human_status" label="人工审核" width="120">
          <template #default="{ row }">
            <el-tag :type="humanTagType(row.human_status)" size="small">
              {{ humanLabel(row.human_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default>
            <el-button link type="primary" size="small">编辑</el-button>
            <el-button link type="success" size="small">通过</el-button>
            <el-button link type="warning" size="small">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const status = ref('all')
const selected = ref<any[]>([])
const drafts = [
  { id: 1, title: '【敏感肌必看】XX 美容院补水修护全流程', channel: 'xiaohongshu', skill: 'article', fact_ok: true, compliance_ok: true, human_status: 'pending' },
  { id: 2, title: 'FAQ：敏感肌能做美容院项目吗？', channel: 'hosted', skill: 'faq', fact_ok: true, compliance_ok: true, human_status: 'approved' },
  { id: 3, title: '2026 夏天油皮怎么选美容院项目', channel: 'zhihu', skill: 'article', fact_ok: false, compliance_ok: true, human_status: 'pending' },
  { id: 4, title: '门店地址与预约方式（到店决策卡）', channel: 'hosted', skill: 'snippet', fact_ok: true, compliance_ok: false, human_status: 'rejected' },
]
function tagType(c: string) {
  return { xiaohongshu: 'danger', zhihu: '', hosted: 'success', dianping: 'warning', douyin: 'info' }[c] || ''
}
function humanTagType(s: string) {
  return { pending: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info'
}
function humanLabel(s: string) {
  return { pending: '待审核', approved: '已通过', rejected: '已驳回' }[s] || s
}
function runProduce() {
  ElMessage.success('S4 阶段实现：启动 GAP→PLAN→EXECUTE→机器审 子图')
}
function bulkApprove() {
  ElMessageBox.confirm(`确认批量通过 ${selected.value.length} 篇草稿？`, '二次确认', { type: 'warning' })
    .then(() => ElMessage.success('已提交（S4 阶段真实写入）'))
    .catch(() => {})
}
</script>

