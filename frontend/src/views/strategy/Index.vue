<template>
  <div>
    <div class="page-header">
      <div>
        <h2>定方案 · StrategyPack</h2>
        <div class="subtitle">五区数据一律来自数据库 API（缺则后端种子写入）</div>
      </div>
      <div>
        <el-button :loading="loading.refresh" @click="refresh">刷新草案</el-button>
        <el-button type="success" :loading="loading.confirm" @click="confirm">确认方案包</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      title="MOCK / 种子数据：五区尚未真接诊断与词库。TODO(WAIT_FOR: A7+A8) 后切 GET /diagnosis + GET /keywords。"
    />
    <el-alert
      type="info"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      title="数据来自数据库。development 下若租户无数据，后端会自动写入演示种子。"
    />
    <el-alert
      v-if="loadError"
      type="error"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      :title="loadError"
    />

    <el-row :gutter="16">
      <el-col :sm="24" :lg="12">
        <div class="page-card zone">
          <div class="zone-label">A · 画像 Persona</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="角色">{{ personaView.role }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ personaView.age }}</el-descriptions-item>
            <el-descriptions-item label="痛点">
              <el-tag v-for="n in personaView.pain_tags" :key="n" size="small" style="margin: 2px">{{ n }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="决策因子">
              <el-tag
                v-for="n in personaView.decision_factors"
                :key="n"
                size="small"
                type="warning"
                style="margin: 2px"
                >{{ n }}</el-tag
              >
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
      <el-col :sm="24" :lg="12">
        <div class="page-card zone">
          <div class="zone-label">B · 竞品 Competitor</div>
          <el-table :data="competitors" size="small" border>
            <el-table-column prop="name" label="竞品" />
            <el-table-column prop="type" label="类型" width="90" />
            <el-table-column prop="differentiation" label="差异化" min-width="160" show-overflow-tooltip />
          </el-table>
          <p v-if="diffBrief" class="hint">{{ diffBrief }}</p>
        </div>
      </el-col>
    </el-row>

    <div class="page-card zone">
      <div class="zone-label">C · 场景 Scenario（勾选 ≤5）</div>
      <el-table
        ref="scenarioTableRef"
        :data="scenarios"
        border
        stripe
        @selection-change="onSelectScenarios"
        @select="onSelectRow"
        @select-all="onSelectAll"
      >
        <el-table-column type="selection" width="48" :selectable="scenarioSelectable" />
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="user_query" label="用户问题" min-width="280" show-overflow-tooltip />
        <el-table-column prop="intent" label="意图" width="120" />
        <el-table-column prop="channel" label="渠道" width="110" />
        <el-table-column prop="skill" label="Skill" width="100" />
      </el-table>
      <div class="hint">已选 {{ selectedIds.length }} / 最多 5（第 6 项起不可勾选）</div>
    </div>

    <div class="page-card zone">
      <div class="zone-label">D · 渠道权重（mixed = 0.6×model + 0.4×probe）</div>
      <div v-for="c in channels" :key="c.name" style="margin-bottom: 14px">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px">
          <span>
            {{ c.name }}
            <el-tag size="small" style="margin-left: 6px">model {{ pct(c.model_weight) }}</el-tag>
            <el-tag size="small" type="warning" style="margin-left: 4px">probe {{ pct(c.probe_weight) }}</el-tag>
          </span>
          <span style="color: #409eff; font-weight: 600">mixed {{ pct(c.mixed_weight) }}</span>
        </div>
        <el-progress :percentage="Math.round((c.mixed_weight || 0) * 100)" :stroke-width="10" />
      </div>
    </div>

    <div class="page-card zone">
      <div class="zone-label">E · 词库 Keywords（折叠）</div>
      <el-collapse>
        <el-collapse-item v-for="(words, layer) in keywordLayers" :key="layer" :title="String(layer)">
          <el-tag v-for="w in words" :key="w.keyword" size="small" style="margin: 4px">
            {{ w.keyword }}
            <span class="src">· {{ w.source }}</span>
          </el-tag>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getStrategyPackDraft,
  confirmStrategyPack,
  type StrategyPackDraftView,
  type ChannelMixed,
} from '@/api/strategy'

const router = useRouter()
const loading = reactive({ refresh: false, confirm: false })
const loadError = ref('')
const pack = ref<StrategyPackDraftView | null>(null)
const selectedIds = ref<string[]>([])
const scenarioTableRef = ref<{ clearSelection?: () => void; toggleRowSelection?: (row: any, selected?: boolean) => void } | null>(null)
const MAX_SCENARIOS = 5

const personaView = computed(() => {
  const p = pack.value?.persona?.buyer_personas?.[0]
  if (!p) return { role: '—', age: '—', pain_tags: [] as string[], decision_factors: [] as string[] }
  return {
    role: p.role || '—',
    age: (p.age_range || []).join('-') || '—',
    pain_tags: p.pain_tags || [],
    decision_factors: p.decision_factors || [],
  }
})

const competitors = computed(() => pack.value?.competitors?.profiles || [])
const diffBrief = computed(() => pack.value?.competitors?.differentiation_brief || '')
const scenarios = computed(() => pack.value?.scenarios?.candidates || [])
const channels = computed<ChannelMixed[]>(() => pack.value?.channels || [])
const keywordLayers = computed(() => pack.value?.keywords?.layers || {})

function pct(v?: number) {
  if (v == null) return '—'
  return `${Math.round(v * 1000) / 10}%`
}

function mixed(model: number, probe: number) {
  return Math.round((model * 0.6 + probe * 0.4) * 1e6) / 1e6
}

function normalizeDraft(data: any): StrategyPackDraftView {
  if (data?.persona?.buyer_personas || data?.scenarios?.candidates) {
    return data as StrategyPackDraftView
  }
  return {
    id: data.id,
    persona: {
      buyer_personas: [
        {
          role: '种子画像',
          age_range: data.persona?.age_range || [25, 35],
          pain_tags: data.persona?.core_needs || [],
          decision_factors: data.persona?.decision_factors || [],
        },
      ],
      content_layout_plan: [],
    },
    competitors: {
      profiles: (data.competitors || []).map((c: any) => ({
        name: c.name,
        type: c.type || 'local',
        differentiation: c.differentiator || c.differentiation || '',
      })),
      differentiation_brief: data.competitors?.differentiation_brief || '',
      content_gaps: data.competitors?.content_gaps || [],
    },
    scenarios: {
      candidates: (data.scenarios || []).map((s: any, i: number) => ({
        id: String(s.id ?? `c${i + 1}`),
        user_query: s.user_query,
        intent: s.intent || '',
        channel: s.channel || 'hosted',
        skill: s.skill || 'faq',
      })),
      recommended_count: 3,
      max: 5,
    },
    channels: (data.channels || []).map((c: any) => ({
      name: c.name,
      model_weight: c.model_weight ?? (c.weight || 0) / 100,
      probe_weight: c.probe_weight ?? 0,
      mixed_weight:
        c.mixed_weight ??
        mixed(c.model_weight ?? (c.weight || 0) / 100, c.probe_weight ?? 0),
      scenario_count: c.scenario_count ?? 1,
    })),
    keywords: data.keywords || { layers: {} },
  }
}

function scenarioSelectable(row: any) {
  if (selectedIds.value.includes(String(row.id))) return true
  return selectedIds.value.length < MAX_SCENARIOS
}

function onSelectScenarios(rows: any[]) {
  if (rows.length > MAX_SCENARIOS) {
    const kept = rows.slice(0, MAX_SCENARIOS)
    selectedIds.value = kept.map((r) => String(r.id))
    ElMessage.warning(`最多勾选 ${MAX_SCENARIOS} 个 scenario`)
    // 回写表格选中态，避免第 6 项仍显示勾选
    const table = scenarioTableRef.value
    if (table?.clearSelection && table?.toggleRowSelection) {
      table.clearSelection()
      kept.forEach((r) => table.toggleRowSelection?.(r, true))
    }
    return
  }
  selectedIds.value = rows.map((r) => String(r.id))
}

function onSelectRow(_selection: any[], _row: any) {
  // selection-change 已处理；保留钩子便于后续埋点
}

function onSelectAll(selection: any[]) {
  if (selection.length > MAX_SCENARIOS) {
    onSelectScenarios(selection)
  }
}

async function refresh() {
  loading.refresh = true
  loadError.value = ''
  try {
    const res: any = await getStrategyPackDraft()
    const data = res?.data ?? res
    if (!data) throw new Error('empty draft')
    pack.value = normalizeDraft(data)
    ElMessage.success('已从数据库加载方案包')
  } catch (e: any) {
    pack.value = null
    loadError.value = e?.message || '方案包 API 失败（请确认后端与 MySQL）'
    ElMessage.error(loadError.value)
  } finally {
    loading.refresh = false
  }
}

async function confirm() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请至少勾选 1 个 scenario（最多 5 个）')
    return
  }
  loading.confirm = true
  try {
    await ElMessageBox.confirm('确认方案包将作为生产与监测基准，是否继续？', '二次确认', {
      type: 'warning',
    })
    const r: any = await confirmStrategyPack({
      selected_scenarios: selectedIds.value,
      persona_confirmed: true,
      competitor_confirmed: true,
    })
    const data = r?.data ?? r
    ElMessage.success('方案包已确认（已写入数据库）')
    router.push(data?.next_route || '/content/drafts')
  } catch (e: any) {
    if (e === 'cancel' || e?.toString?.().includes('cancel')) return
    ElMessage.error(e?.message || '确认失败')
  } finally {
    loading.confirm = false
  }
}

onMounted(refresh)
</script>

<style scoped>
.zone-label {
  font-weight: 700;
  margin-bottom: 12px;
  font-size: 15px;
}
.hint {
  margin-top: 8px;
  color: #909399;
  font-size: 13px;
}
.src {
  color: #909399;
  font-size: 11px;
}
</style>
