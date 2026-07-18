<template>
  <div>
    <div class="page-header">
      <div>
        <h2>效果舱 Dashboard</h2>
        <div class="subtitle">
          T0/T1 Δ · 四层漏斗 · GEO 效率
          <!-- TODO(WAIT_FOR: A7) 真 T0 KPI -->
        </div>
      </div>
      <div>
        <el-button @click="reload">刷新</el-button>
        <el-radio-group v-model="period" size="default" @change="reload">
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="quarter">本季度</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-alert
      :type="loadError ? 'error' : dash?.waiting_for_a7 ? 'warning' : 'info'"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
      :title="
        loadError ||
        (dash?.waiting_for_a7
          ? '尚无真 T0 · TODO(WAIT_FOR: A7)。可先在监测页种假 T0 再看 Δ。'
          : '数据来自 GET /outcomes/dashboard，与监测 T0/T1 汇总一致。')
      "
    />

    <div class="stat-grid" style="margin-bottom: 16px">
      <div class="kpi-card">
        <div class="accent-bar"></div>
        <div class="label">T0 提及率</div>
        <div class="value">{{ pct(kpi?.mention_rate_t0) }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#67c23a"></div>
        <div class="label">T1 提及率</div>
        <div class="value">{{ pct(kpi?.mention_rate_t1) }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#e6a23c"></div>
        <div class="label">Δ mention</div>
        <div class="value">{{ signedPct(kpi?.delta_mention) }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#f56c6c"></div>
        <div class="label">幻觉率</div>
        <div class="value">{{ pct(kpi?.hallucination_rate) }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#909399"></div>
        <div class="label">已发布</div>
        <div class="value">{{ kpi?.total_drafts_published ?? '—' }}</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#a855f7"></div>
        <div class="label">GEO 效率</div>
        <div class="value">{{ dash?.geo_efficiency ?? '—' }}</div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="14">
        <div class="page-card">
          <h3 style="margin-top:0">四层漏斗</h3>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="exposure 曝光">
              <el-tag :type="funnel?.exposure?.ok ? 'success' : 'info'" size="small">
                {{ funnel?.exposure?.ok ? 'ok' : '未通' }}
              </el-tag>
              · 已发布 {{ funnel?.exposure?.published ?? 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="trust 信任">
              <el-tag :type="funnel?.trust?.ok ? 'success' : 'info'" size="small">
                {{ funnel?.trust?.ok ? 'ok' : '未通' }}
              </el-tag>
              · avg_trust {{ funnel?.trust?.avg_trust_score ?? '—' }}
            </el-descriptions-item>
            <el-descriptions-item label="leads 线索">
              form_submits = {{ funnel?.leads?.form_submits ?? 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="conversion 转化">
              cost={{ funnel?.conversion?.manual_cost ?? 'null' }} · revenue={{
                funnel?.conversion?.manual_revenue ?? 'null'
              }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="page-card">
          <h3 style="margin-top:0">Core 提及率趋势</h3>
          <v-chart class="chart-sm" :option="chartOption" autoresize />
        </div>
      </el-col>
    </el-row>

    <div class="page-card" style="margin-top: 16px">
      <h3 style="margin-top:0">告警 / 建议</h3>
      <el-empty v-if="!(dash?.alerts || []).length" description="暂无告警" />
      <el-alert
        v-for="(a, i) in dash?.alerts || []"
        :key="i"
        :type="alertType(a.level)"
        show-icon
        class="alert-item"
        :title="a.msg || a.type"
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getDashboard } from '@/api/ops'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])
void VChart

const period = ref<'week' | 'month' | 'quarter'>('week')
const loading = ref(false)
const loadError = ref('')
const dash = ref<any>(null)

const kpi = computed(() => dash.value?.kpi)
const funnel = computed(() => dash.value?.funnel)

function pct(v: number | undefined | null) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return `${Math.round(Number(v) * 1000) / 10}%`
}
function signedPct(v: number | undefined | null) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  const n = Math.round(Number(v) * 1000) / 10
  return `${n >= 0 ? '+' : ''}${n}%`
}
function alertType(level: string) {
  return ({ critical: 'error', warning: 'warning', info: 'info' } as Record<string, string>)[level] || 'info'
}

const chartOption = computed(() => {
  const trend = dash.value?.trend || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: trend.map((t: any) => t.date) },
    yAxis: { type: 'value', axisLabel: { formatter: (v: number) => `${Math.round(v * 100)}%` } },
    series: [
      {
        name: 'mention_rate',
        type: 'line',
        smooth: true,
        data: trend.map((t: any) => Math.round((t.mention_rate || 0) * 1000) / 10),
        itemStyle: { color: '#409eff' },
      },
    ],
  }
})

async function reload() {
  loading.value = true
  loadError.value = ''
  try {
    const res: any = await getDashboard(period.value)
    dash.value = res?.data || res
  } catch (e: any) {
    dash.value = null
    loadError.value = e?.message || '效果舱 API 失败'
    ElMessage.error(loadError.value)
  } finally {
    loading.value = false
  }
}

watch(period, () => reload())
onMounted(reload)
</script>

<style scoped>
.chart-sm {
  height: 260px;
}
.alert-item {
  margin-bottom: 10px;
}
</style>
