<template>
  <div>
    <div class="page-header">
      <div>
        <h2>📊 效果舱 Dashboard</h2>
        <div class="subtitle">AI 信任资产 → 分渠道可见度 → 转化闭环</div>
      </div>
      <el-radio-group v-model="period" size="default">
        <el-radio-button label="week">本周</el-radio-button>
        <el-radio-button label="month">本月</el-radio-button>
        <el-radio-button label="quarter">本季度</el-radio-button>
      </el-radio-group>
    </div>

    <div class="stat-grid" style="margin-bottom: 16px">
      <div class="kpi-card">
        <div class="accent-bar"></div>
        <div class="label">已覆盖 Scenario</div>
        <div class="value">12</div>
        <div class="trend up">↑ 本周 +3 新场景</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#67c23a"></div>
        <div class="label">已发布内容</div>
        <div class="value">27</div>
        <div class="trend up">↑ +8</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#e6a23c"></div>
        <div class="label">Core 提及率</div>
        <div class="value">38.5%</div>
        <div class="trend up">↑ +6.2pp</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#f56c6c"></div>
        <div class="label">平均 AI 信任度</div>
        <div class="value">76.3</div>
        <div class="trend up">↑ +4.1</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#909399"></div>
        <div class="label">Probe 发现</div>
        <div class="value">5</div>
        <div class="trend">新增信源候选</div>
      </div>
      <div class="kpi-card">
        <div class="accent-bar" style="background:#a855f7"></div>
        <div class="label">转化闭环入口</div>
        <div class="value">143</div>
        <div class="trend up">↑ 托管页点击 +21%</div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="16">
        <div class="page-card">
          <h3 style="margin-top:0">📈 Core 提及率趋势（按引擎）</h3>
          <v-chart class="chart" :option="chartOption" autoresize />
        </div>
      </el-col>
      <el-col :span="8">
        <div class="page-card">
          <h3 style="margin-top:0">🧭 分渠道可见度</h3>
          <v-chart class="chart-sm" :option="pieOption" autoresize />
        </div>
      </el-col>
    </el-row>

    <div class="page-card">
      <h3 style="margin-top:0">🔔 临界触发与建议迭代</h3>
      <el-alert type="warning" show-icon class="alert-item" title="【敏感肌修护】连续 2 周 Core 提及率低于 20%"
        description="建议：补充 1 条 FAQ + 1 篇小红书笔记，人工确认后写入方案包。" :closable="false">
        <template #action>
          <el-button size="small" type="warning" plain>生成草案</el-button>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])
void VChart

const period = ref('week')
const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['豆包', 'DeepSeek', 'Kimi', '文心'] },
  grid: { left: 40, right: 20, top: 40, bottom: 30 },
  xAxis: { type: 'category', data: ['W-4', 'W-3', 'W-2', 'W-1', '本周'] },
  yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
  series: [
    { name: '豆包', type: 'line', smooth: true, data: [24, 26, 29, 33, 38], itemStyle: { color: '#409eff' } },
    { name: 'DeepSeek', type: 'line', smooth: true, data: [19, 22, 25, 28, 34], itemStyle: { color: '#67c23a' } },
    { name: 'Kimi', type: 'line', smooth: true, data: [15, 17, 20, 23, 27], itemStyle: { color: '#e6a23c' } },
    { name: '文心', type: 'line', smooth: true, data: [10, 13, 16, 19, 22], itemStyle: { color: '#f56c6c' } },
  ],
}))
const pieOption = {
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['45%', '70%'],
      avoidLabelOverlap: true,
      label: { formatter: '{b}\n{d}%' },
      data: [
        { value: 38, name: '托管页', itemStyle: { color: '#409eff' } },
        { value: 25, name: '小红书', itemStyle: { color: '#f56c6c' } },
        { value: 15, name: '知乎', itemStyle: { color: '#67c23a' } },
        { value: 14, name: '点评', itemStyle: { color: '#e6a23c' } },
        { value: 8, name: '其他', itemStyle: { color: '#909399' } },
      ],
    },
  ],
}
</script>

<style scoped>
.chart {
  height: 320px;
}
.chart-sm {
  height: 280px;
}
.alert-item {
  margin-bottom: 10px;
}
</style>
