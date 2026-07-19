<template>
  <div>
    <div class="page-header">
      <div>
        <h2>AI 监测体系</h2>
        <div class="subtitle">
          Core ~20 · Probe ≤10 · T1 写入 · Δ（假 T0 WAIT_FOR A7）
        </div>
      </div>
      <div>
        <el-button @click="reload">刷新</el-button>
        <el-button @click="doSeedT0">种假 T0</el-button>
        <el-button @click="doTrigger('core')">触发 Core(T1)</el-button>
        <el-button type="primary" @click="doTrigger('probe')">触发 Probe(T1)</el-button>
      </div>
    </div>

    <el-alert
      :type="loadError ? 'error' : 'info'"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      :title="
        loadError ||
        '数据来自 monitor_results。T1=baseline false；真 T0 等 A7，开发态可种假 T0。'
      "
    />

    <div class="stat-grid" style="margin-bottom: 16px">
      <div class="kpi-card">
        <div class="accent-bar"></div>
        <div class="label">引擎</div>
        <div class="value engines">{{ (profile?.target_engines || []).join(' · ') || '—' }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#67c23a"></div>
        <div class="label">T0 提及率</div>
        <div class="value">{{ pct(delta?.mention_rate_t0) }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#409eff"></div>
        <div class="label">T1 提及率</div>
        <div class="value">{{ pct(delta?.mention_rate_t1) }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#e6a23c"></div>
        <div class="label">Δ mention</div>
        <div class="value">{{ signedPct(delta?.delta_mention) }}</div>
      </div>
    </div>
    <p v-if="delta?.waiting_for_a7" class="hint">尚无真 T0 · TODO(WAIT_FOR: A7)</p>

    <el-row :gutter="16">
      <el-col :span="12">
        <div class="page-card">
          <h3 style="margin-top:0">Core 主池（含 T0/T1）</h3>
          <el-table :data="coreResults" border stripe size="small" v-loading="loading">
            <el-table-column prop="engine" label="引擎" width="90" />
            <el-table-column prop="query" label="查询" min-width="180" show-overflow-tooltip />
            <el-table-column prop="baseline" label="基线" width="70">
              <template #default="{ row }">
                <el-tag size="small" :type="row.baseline ? 'warning' : 'success'">
                  {{ row.baseline ? 'T0' : 'T1' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="mentioned" label="提及" width="70">
              <template #default="{ row }">
                <el-tag v-if="row.mentioned" size="small" type="success">是</el-tag>
                <el-tag v-else size="small" type="info">否</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="trust_score" label="信任" width="70">
              <template #default="{ row }">
                {{ row.trust_score != null ? Math.round(Number(row.trust_score) * 100) : '—' }}
              </template>
            </el-table-column>
            <el-table-column prop="position_rank" label="排名" width="60" align="center" />
          </el-table>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="page-card">
          <h3 style="margin-top:0">Probe 探针池</h3>
          <el-table :data="probeResults" border stripe size="small" v-loading="loading">
            <el-table-column prop="engine" label="引擎" width="90" />
            <el-table-column prop="query" label="Query" min-width="200" show-overflow-tooltip />
            <el-table-column prop="mentioned" label="提及" width="70">
              <template #default="{ row }">
                <el-tag size="small" :type="row.mentioned ? 'danger' : 'info'">
                  {{ row.mentioned ? '有' : '无' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="batch_no" label="批次" min-width="120" show-overflow-tooltip />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listCore,
  listProbe,
  triggerMonitor,
  getMonitorProfile,
  getMonitorDelta,
  seedMonitorT0,
} from '@/api/ops'

const loading = ref(false)
const loadError = ref('')
const coreResults = ref<any[]>([])
const probeResults = ref<any[]>([])
const profile = ref<any>(null)
const delta = ref<any>(null)

function pct(v: number | undefined | null) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return `${Math.round(Number(v) * 100)}%`
}
function signedPct(v: number | undefined | null) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Math.round(Number(v) * 100)
  return `${n >= 0 ? '+' : ''}${n}%`
}

async function reload() {
  loading.value = true
  loadError.value = ''
  try {
    const [p, d, c, pr] = await Promise.all([
      getMonitorProfile(),
      getMonitorDelta('core'),
      listCore({ page: 1, page_size: 30 }),
      listProbe({ page: 1, page_size: 30 }),
    ])
    profile.value = (p as any)?.data || p
    delta.value = (d as any)?.data || d
    const cData = (c as any)?.data
    const pData = (pr as any)?.data
    coreResults.value = Array.isArray(cData) ? cData : cData?.items || []
    probeResults.value = Array.isArray(pData) ? pData : pData?.items || []
  } catch (e: any) {
    loadError.value = e?.message || '监测 API 失败'
    ElMessage.error(loadError.value)
  } finally {
    loading.value = false
  }
}

async function doTrigger(pool: 'core' | 'probe') {
  try {
    const res: any = await triggerMonitor(pool)
    ElMessage.success(`已写 T1 ${res?.data?.created ?? ''} 条`)
    await reload()
  } catch (e: any) {
    ElMessage.error(e?.message || '触发失败')
  }
}

async function doSeedT0() {
  try {
    const res: any = await seedMonitorT0()
    ElMessage.success(`假 T0：${res?.data?.created ?? 0} 条（WAIT_FOR A7）`)
    await reload()
  } catch (e: any) {
    ElMessage.error(e?.message || '种 T0 失败')
  }
}

onMounted(reload)
</script>

<style scoped>
.engines {
  font-size: 16px;
  line-height: 1.3;
}
.hint {
  color: #e6a23c;
  margin: -8px 0 16px;
  font-size: 13px;
}
</style>
