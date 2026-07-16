<template>
  <div>
    <div class="page-header">
      <div>
        <h2>定方案 · StrategyPack</h2>
        <div class="subtitle">
          五区：A 画像 · B 竞品 · C 场景 · D 渠道 · E 词库
          <!-- TODO(WAIT_FOR: A-fixture) 官方 handoff 四文件由 A 提交后替换本地 mock -->
        </div>
      </div>
      <div>
        <el-button :loading="loading.refresh" @click="refresh">刷新草案</el-button>
        <el-button type="success" :loading="loading.confirm" @click="confirm">确认方案包</el-button>
      </div>
    </div>

    <el-alert
      v-if="usingMock"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      title="当前为 MOCK 数据（本地 handoff）。TODO(WAIT_FOR: A7+A8 / A-fixture) 真接后自动切换。"
    />

    <el-row :gutter="16">
      <el-col :sm="24" :lg="12">
        <div class="page-card zone">
          <div class="zone-label">A · 画像 Persona</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="角色">{{ personaView.role }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ personaView.age }}</el-descriptions-item>
            <el-descriptions-item label="痛点">
              <el-tag v-for="n in personaView.pain_tags" :key="n" size="small" style="margin:2px">{{ n }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="决策因子">
              <el-tag v-for="n in personaView.decision_factors" :key="n" size="small" type="warning" style="margin:2px">{{ n }}</el-tag>
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
      <el-table :data="scenarios" border stripe @selection-change="onSelectScenarios">
        <el-table-column type="selection" width="48" :selectable="() => selectedIds.length < 5 || true" />
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="user_query" label="用户问题" min-width="280" show-overflow-tooltip />
        <el-table-column prop="intent" label="意图" width="120" />
        <el-table-column prop="channel" label="渠道" width="110" />
        <el-table-column prop="skill" label="Skill" width="100" />
      </el-table>
      <div class="hint">已选 {{ selectedIds.length }} / 最多 5</div>
    </div>

    <div class="page-card zone">
      <div class="zone-label">D · 渠道权重（mixed = 0.6×model + 0.4×probe）</div>
      <div v-for="c in channels" :key="c.name" style="margin-bottom: 14px">
        <div style="display:flex; justify-content:space-between; margin-bottom: 6px">
          <span>
            {{ c.name }}
            <el-tag size="small" style="margin-left:6px">model {{ pct(c.model_weight) }}</el-tag>
            <el-tag size="small" type="warning" style="margin-left:4px">probe {{ pct(c.probe_weight) }}</el-tag>
          </span>
          <span style="color:#409eff; font-weight:600">mixed {{ pct(c.mixed_weight) }}</span>
        </div>
        <el-progress :percentage="Math.round((c.mixed_weight || 0) * 100)" :stroke-width="10" />
      </div>
    </div>

    <div class="page-card zone">
      <div class="zone-label">E · 词库 Keywords（折叠）</div>
      <el-collapse>
        <el-collapse-item v-for="(words, layer) in keywordLayers" :key="layer" :title="String(layer)">
          <el-tag v-for="w in words" :key="w.keyword" size="small" style="margin:4px">
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
import handoffMock from '@/mocks/handoff_a_to_b.json'

const router = useRouter()
const loading = reactive({ refresh: false, confirm: false })
const usingMock = ref(true)
const pack = ref<StrategyPackDraftView | null>(null)
const selectedIds = ref<string[]>([])

const personaView = computed(() => {
  const p = pack.value?.persona?.buyer_personas?.[0]
  if (p) {
    return {
      role: p.role || '—',
      age: (p.age_range || []).join('-') || '—',
      pain_tags: p.pain_tags || [],
      decision_factors: p.decision_factors || [],
    }
  }
  return {
    role: '静安寺白领女性（MOCK）',
    age: '25-35',
    pain_tags: ['敏感肌', '怕推销'],
    decision_factors: ['口碑', '资质', '距离'],
  }
})

const competitors = computed(() => {
  const fromPack = pack.value?.competitors?.profiles
  if (fromPack?.length) return fromPack
  return (handoffMock.diagnosis.competitor_analysis || []).map((c: any) => ({
    name: c.name,
    type: c.type,
    differentiation: c.differentiation || c.differentiator || '',
  }))
})

const diffBrief = computed(
  () => pack.value?.competitors?.differentiation_brief || '差异化：透明价格 + 成分公开 + 1v1（MOCK）',
)

const scenarios = computed(() => {
  const c = pack.value?.scenarios?.candidates
  if (c?.length) return c
  return [
    { id: 'c1', user_query: '敏感肌能不能做皮肤管理', intent: '项目咨询', channel: 'hosted', skill: 'faq' },
    { id: 'c2', user_query: '静安寺附近做脸哪家不推销', intent: '到店决策', channel: 'xiaohongshu', skill: 'article' },
    { id: 'c3', user_query: 'XX皮肤管理和YY美容院怎么选', intent: '选型对比', channel: 'zhihu', skill: 'comparison' },
  ]
})

const channels = computed<ChannelMixed[]>(() => {
  if (pack.value?.channels?.length) return pack.value.channels
  return buildChannelsFromMock()
})

const keywordLayers = computed(() => {
  const layers = pack.value?.keywords?.layers
  if (layers && Object.keys(layers).length) return layers
  const grouped: Record<string, any[]> = { 选型层: [], 场景层: [], 痛点层: [], 认知层: [] }
  for (const k of handoffMock.keywords || []) {
    const layer = k.layer || '选型层'
    if (!grouped[layer]) grouped[layer] = []
    grouped[layer].push(k)
  }
  return grouped
})

function pct(v?: number) {
  if (v == null) return '—'
  return `${Math.round(v * 1000) / 10}%`
}

/** mixed_weight = model*0.6 + probe*0.4 */
function mixed(model: number, probe: number) {
  return Math.round((model * 0.6 + probe * 0.4) * 1e6) / 1e6
}

function buildChannelsFromMock(): ChannelMixed[] {
  // TODO(WAIT_FOR: A7) probe weights from real source_map
  const rankings = handoffMock.diagnosis?.source_map?.rankings || []
  const probeByHint: Record<string, number> = {
    AI托管页: 0.1,
    小红书: 0.05,
    知乎: rankings.find((r: any) => String(r.domain).includes('zhihu'))?.weight || 0.15,
    大众点评: rankings.find((r: any) => String(r.domain).includes('dianping'))?.weight || 0.2,
  }
  const defaults = [
    { name: 'AI托管页', model_weight: 0.4, probe_weight: probeByHint['AI托管页'] },
    { name: '小红书', model_weight: 0.25, probe_weight: probeByHint['小红书'] },
    { name: '知乎', model_weight: 0.1, probe_weight: probeByHint['知乎'] },
    { name: '大众点评', model_weight: 0.15, probe_weight: probeByHint['大众点评'] },
  ]
  return defaults.map((d) => ({
    ...d,
    mixed_weight: mixed(d.model_weight, d.probe_weight),
    scenario_count: 1,
  }))
}

function buildMockPack(): StrategyPackDraftView {
  return {
    id: 0,
    persona: {
      buyer_personas: [
        {
          role: '静安寺白领女性',
          age_range: [25, 35],
          pain_tags: ['敏感肌', '怕推销', '午休短'],
          decision_factors: ['口碑', '资质', '距离'],
          trust_triggers: ['VISIA报告', '评价带图'],
        },
      ],
      content_layout_plan: [
        { persona: '敏感肌白领', content_type: 'FAQ+场景推荐', channel: '小红书+知乎', cta: '预约小程序' },
      ],
    },
    competitors: {
      profiles: competitors.value,
      differentiation_brief: diffBrief.value,
      content_gaps: handoffMock.diagnosis?.source_map?.gaps || [],
    },
    scenarios: {
      candidates: scenarios.value as any,
      recommended_count: 3,
      max: 5,
    },
    channels: buildChannelsFromMock(),
    keywords: { layers: keywordLayers.value as any },
    kb_freshness: { warning: false, updated_at: new Date().toISOString() },
  }
}

function onSelectScenarios(rows: any[]) {
  selectedIds.value = rows.map((r) => String(r.id)).slice(0, 5)
}

async function refresh() {
  loading.refresh = true
  try {
    const r: any = await getStrategyPackDraft()
    const data = r?.data ?? r
    if (data && (data.persona || data.channels || data.scenarios)) {
      // Normalize legacy API shape into five-zone view when needed
      if (data.persona?.buyer_personas || data.scenarios?.candidates) {
        pack.value = data as StrategyPackDraftView
      } else {
        pack.value = {
          id: data.id,
          persona: {
            buyer_personas: [
              {
                role: (data.persona?.cities || []).join('·') || '本地客户',
                age_range: data.persona?.age_range || [25, 45],
                pain_tags: data.persona?.core_needs || [],
                decision_factors: data.persona?.decision_factors || [],
                trust_triggers: [],
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
            differentiation_brief: '',
            content_gaps: [],
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
            mixed_weight: c.mixed_weight ?? mixed(c.model_weight ?? (c.weight || 0) / 100, c.probe_weight ?? 0),
            scenario_count: c.scenario_count ?? 1,
          })),
          keywords: data.keywords || { layers: keywordLayers.value as any },
        }
      }
      usingMock.value = false
      ElMessage.success('已从 API 刷新草案')
      return
    }
    throw new Error('empty draft')
  } catch {
    // TODO(WAIT_FOR: A7+A8) real diagnosis/keywords
    pack.value = buildMockPack()
    usingMock.value = true
    ElMessage.info('API 不可用，已加载本地 MOCK 五区')
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
    await ElMessageBox.confirm('确认方案包将作为生产与监测基准，是否继续？', '二次确认', { type: 'warning' })
    const r: any = await confirmStrategyPack({
      selected_scenarios: selectedIds.value,
      persona_confirmed: true,
      competitor_confirmed: true,
    })
    const data = r?.data ?? r
    ElMessage.success('方案包已确认')
    const next = data?.next_route || '/content/drafts'
    router.push(next)
  } catch (e: any) {
    if (e === 'cancel' || e?.toString?.().includes('cancel')) return
    // MOCK confirm path when API fails
    ElMessage.warning('确认 API 未就绪，MOCK 跳转草稿页（TODO WAIT_FOR backend B2）')
    router.push('/content/drafts')
  } finally {
    loading.confirm = false
  }
}

onMounted(() => {
  pack.value = buildMockPack()
  usingMock.value = true
  refresh()
})
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
