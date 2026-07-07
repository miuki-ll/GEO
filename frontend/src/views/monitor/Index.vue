<template>
  <div>
    <div class="page-header">
      <div>
        <h2>🔍 AI 监测体系</h2>
        <div class="subtitle">Core 主池（~20 query 周更）· Probe 探针池（≤10 探测新信源）</div>
      </div>
      <div>
        <el-tag type="warning" effect="dark" style="margin-right:12px">最近批次：2026-W27</el-tag>
        <el-button @click="triggerCore">触发 Core 轮询</el-button>
        <el-button type="primary" @click="triggerProbe">触发 Probe 探测</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <div class="page-card">
          <h3 style="margin-top:0">🧪 Core 主池</h3>
          <el-table :data="coreResults" border stripe size="small">
            <el-table-column prop="engine" label="引擎" width="100" />
            <el-table-column prop="query" label="查询" min-width="260" show-overflow-tooltip />
            <el-table-column prop="mentioned" label="提及" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.mentioned" size="small" type="success">是</el-tag>
                <el-tag v-else size="small" type="info">否</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="trust" label="信任度" width="90">
              <template #default="{ row }">
                <el-progress :percentage="row.trust" :stroke-width="8" :color="row.trust>=70?'#67c23a':row.trust>=40?'#e6a23c':'#f56c6c'" />
              </template>
            </el-table-column>
            <el-table-column prop="rank" label="排名" width="70" align="center" />
          </el-table>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="page-card">
          <h3 style="margin-top:0">🛰️ Probe 探针池</h3>
          <el-table :data="probeResults" border stripe size="small">
            <el-table-column prop="engine" label="引擎" width="100" />
            <el-table-column prop="query" label="新信源 Query" min-width="240" show-overflow-tooltip />
            <el-table-column prop="found" label="发现新信源" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="row.found?'danger':'info'">{{ row.found ? '有 ✅' : '无' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="备注" min-width="140" show-overflow-tooltip />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button v-if="row.found" link type="primary" size="small" @click="toCore(row)">入 Core 候选</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
const coreResults = [
  { engine: '豆包', query: 'XX区做敏感肌修护推荐哪家美容院？', mentioned: true, trust: 82, rank: 2 },
  { engine: 'DeepSeek', query: 'XX区做敏感肌修护推荐哪家美容院？', mentioned: true, trust: 74, rank: 3 },
  { engine: 'Kimi', query: 'XX区做敏感肌修护推荐哪家美容院？', mentioned: false, trust: 0, rank: '-' },
  { engine: '文心', query: '夏天油皮补水美容院做什么项目比较好？', mentioned: true, trust: 61, rank: 4 },
]
const probeResults = [
  { engine: '豆包', query: 'XX路附近的皮肤管理推荐', found: true, note: '发现 2 家新竞品提及' },
  { engine: 'Kimi', query: '换季泛红美容院做什么项目好', found: false, note: '尚未出提及' },
  { engine: 'DeepSeek', query: '平价补水美容店 XX 市', found: true, note: '可入 Core：gap > 20%' },
]
function triggerCore() {
  ElMessage.success('S5 阶段实现：Celery 调度 Core 轮询任务')
}
function triggerProbe() {
  ElMessage.success('S5 阶段实现：Celery 调度 Probe 探测')
}
function toCore(row: any) {
  ElMessageBox.confirm(`将「${row.query}」评估后加入 Core 候选池？`, '入 Core 候选', { type: 'success' })
    .then(() => ElMessage.success('已加入候选评估队列'))
    .catch(() => {})
}
</script>

