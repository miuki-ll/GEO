<template>
  <div>
    <div class="page-header">
      <div>
        <h2>📘 定方案 · StrategyPack</h2>
        <div class="subtitle">画像 / 竞品 / 场景 / 渠道 · 一页总览</div>
      </div>
      <div>
        <el-button :loading="loading.refresh" @click="refresh">🔄 刷新草案</el-button>
        <el-button type="success" :disabled="!confirmedData" :loading="loading.confirm" @click="confirm">
          ✅ 确认方案包
        </el-button>
      </div>
    </div>

    <div style="margin-bottom: 16px">
      <el-alert
        v-if="pack?.status==='confirmed'"
        type="success"
        show-icon
        :closable="false"
        :title="`方案包 v${pack?.version || '1.0'} 已于 ${pack?.confirmed_at} 确认`"
      />
      <el-alert v-else type="info" show-icon :closable="false" title="当前展示为草案，S4 诊断链会产出正式版本" />
    </div>

    <el-row :gutter="16">
      <el-col :sm="24" :lg="8">
        <div class="page-card">
          <h3 style="margin-top:0">👥 用户画像 Persona</h3>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="年龄层">{{ persona.age_range?.join('-') || '25-45 岁' }}</el-descriptions-item>
            <el-descriptions-item label="性别 / 地域">{{ (persona.genders||[]).join('、') || '女性为主' }} · {{ (persona.cities||[]).join('、') || '本地 3km' }}</el-descriptions-item>
            <el-descriptions-item label="核心诉求">
              <el-tag v-for="n in persona.core_needs || ['补水','抗衰','敏感肌修护']" :key="n" size="small" style="margin:2px">{{ n }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="决策因子">
              <el-tag v-for="n in persona.decision_factors || ['口碑','资质','距离','价格']" :key="n" size="small" type="warning" style="margin:2px">{{ n }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
      <el-col :sm="24" :lg="8">
        <div class="page-card">
          <h3 style="margin-top:0">🏁 竞品分析 Competitor</h3>
          <el-table :data="competitors" size="small" border>
            <el-table-column prop="name" label="竞品" />
            <el-table-column label="AI提及" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.ai_mention_rate>=30?'danger':row.ai_mention_rate>=15?'warning':'info'">
                  {{ row.ai_mention_rate }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="differentiator" label="差异化" min-width="160" show-overflow-tooltip />
          </el-table>
        </div>
      </el-col>
      <el-col :sm="24" :lg="8">
        <div class="page-card">
          <h3 style="margin-top:0">📡 渠道权重 Channels</h3>
          <div v-for="c in channels" :key="c.name" style="margin-bottom: 14px">
            <div style="display:flex; justify-content:space-between; margin-bottom: 6px">
              <div>
                {{ c.name }}
                <el-tag size="small" :type="c.mode==='auto'?'success':c.mode==='semi'?'warning':'info'" style="margin-left:6px">{{ c.mode?.toUpperCase() }}</el-tag>
              </div>
              <span style="color:#409eff; font-weight:600">{{ c.weight }}%</span>
            </div>
            <el-progress :percentage="c.weight || 0" :stroke-width="10" />
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="page-card">
      <h3 style="margin-top:0">🎯 Scenario 场景清单（MVP-A 首轮）</h3>
      <div style="display:flex; justify-content:space-between; margin-bottom:12px">
        <el-tag type="success">MVP-A 首发：scenario 2 个 · 托管页 AUTO + 1 渠道 SEMI</el-tag>
        <el-button size="small" @click="scenarioDrawer = true">+ 手工添加 Scenario</el-button>
      </div>
      <el-table :data="scenarios" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="user_query" label="用户问题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="intent" label="意图" width="120" />
        <el-table-column prop="channel" label="渠道" width="110">
          <template #default="{ row }"><el-tag size="small">{{ row.channel }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="skill" label="Skill" width="100" />
        <el-table-column prop="target_engines" label="引擎" width="140">
          <template #default="{ row }">
            <el-tag v-for="e in (row.target_engines || [])" :key="e" size="small" style="margin:2px">{{ e }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.priority<=1?'danger':row.priority<=3?'warning':'info'">P{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer v-model="scenarioDrawer" title="新增 Scenario" size="480px">
      <el-form label-width="120px">
        <el-form-item label="用户问题"><el-input v-model="formScenario.user_query" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="意图"><el-input v-model="formScenario.intent" placeholder="如：到店决策 / 项目咨询…" /></el-form-item>
        <el-form-item label="渠道"><el-input v-model="formScenario.channel" /></el-form-item>
        <el-form-item label="Skill">
          <el-select v-model="formScenario.skill" style="width:100%">
            <el-option label="FAQ" value="faq" />
            <el-option label="文章 Article" value="article" />
            <el-option label="片段 Snippet" value="snippet" />
            <el-option label="点评条目" value="review" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-rate v-model="formScenario.priority" :max="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scenarioDrawer = false">取消</el-button>
        <el-button type="primary" @click="addScenario">确认添加</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStrategyPackDraft, confirmStrategyPack, type ScenarioItem, type StrategyPackDraft } from '@/api/strategy'

const loading = reactive({ refresh: false, confirm: false })
const pack = ref<StrategyPackDraft | null>(null)
const persona = ref<any>({})
const competitors = ref<any[]>([])
const channels = ref<any[]>([])
const scenarios = ref<ScenarioItem[]>([])
const scenarioDrawer = ref(false)
const confirmedData = ref(true)
const formScenario = reactive<ScenarioItem>({
  title: '', user_query: '', intent: '', channel: '托管页', skill: 'faq',
  priority: 3, target_engines: ['豆包', 'DeepSeek'],
})

async function refresh() {
  loading.refresh = true
  try {
    const r = await getStrategyPackDraft()
    pack.value = r.data || null
    persona.value = pack.value?.persona || persona.value
    competitors.value = pack.value?.competitors || competitors.value
    scenarios.value = pack.value?.scenarios || scenarios.value
    if (pack.value?.channels?.length) {
      channels.value = pack.value.channels
    }
    ElMessage.success(r.message || '已刷新')
  } finally {
    loading.refresh = false
  }
}
async function confirm() {
  loading.confirm = true
  try {
    await ElMessageBox.confirm('确认方案包将作为生产与监测基准，是否继续？', '二次确认', { type: 'warning' })
    const r = await confirmStrategyPack()
    pack.value = r.data || pack.value
    ElMessage.success('方案包已确认，可前往内容草稿')
  } catch (e) {} finally {
    loading.confirm = false
  }
}
function addScenario() {
  scenarios.value.unshift({
    id: Date.now(),
    ...formScenario,
    title: formScenario.user_query.slice(0, 30),
  } as ScenarioItem)
  scenarioDrawer.value = false
  ElMessage.success('已加入本地清单（S4 将正式写入）')
}
onMounted(() => {
  competitors.value = [
    { name: '连锁品牌A', ai_mention_rate: 42, differentiator: '本地化+客制化服务' },
    { name: '附近门店B', ai_mention_rate: 18, differentiator: '资质齐全+成分透明' },
    { name: '工作室C', ai_mention_rate: 5, differentiator: '卫生/发票正规流程' },
  ]
  channels.value = [
    { name: 'AI 托管页', weight: 40, mode: 'auto' },
    { name: '小红书', weight: 25, mode: 'semi' },
    { name: '知乎', weight: 15, mode: 'semi' },
    { name: '大众点评', weight: 15, mode: 'guided' },
    { name: '抖音', weight: 5, mode: 'guided' },
  ]
  scenarios.value = [
    { id: 1, title: '敏感肌推荐', user_query: 'XX区做敏感肌修护推荐哪家美容院？', intent: '到店决策', channel: '托管页', skill: 'faq', priority: 1, target_engines: ['豆包', 'DeepSeek', 'Kimi', '文心'] },
    { id: 2, title: '油皮补水项目', user_query: '夏天油皮补水美容院做什么项目比较好？', intent: '项目咨询', channel: '小红书', skill: 'article', priority: 2, target_engines: ['豆包', 'DeepSeek'] },
  ]
  refresh()
})
</script>
