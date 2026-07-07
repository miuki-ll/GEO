<template>
  <div>
    <div class="page-header">
      <div>
        <h2>🚀 懂我 · 开店向导</h2>
        <div class="subtitle">8 步完成企业接入 → 生成方案包 → 出首轮内容</div>
      </div>
      <div style="display:flex; gap:10px">
        <el-tag v-if="store.status==='running'" type="warning" effect="dark">
          <el-icon class="is-loading" style="margin-right:4px"><Loading /></el-icon>
          Agent 执行中 {{ store.progress }}%
        </el-tag>
        <el-tag v-else-if="store.status==='done'" type="success" effect="dark">已完成</el-tag>
        <el-button plain @click="store.reset()" :disabled="store.status==='running'">重新开始</el-button>
        <el-button type="primary" @click="start" :disabled="store.status==='running'">
          {{ store.status==='idle' ? '立即开始' : store.status==='running' ? '运行中…' : '继续/重跑' }}
        </el-button>
      </div>
    </div>

    <div class="page-card">
      <ProgressChain
        :steps="store.steps"
        :active="store.currentStep"
        @change="onStepChange"
      />
    </div>

    <div class="page-card">
      <template v-if="store.currentStep === 0">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">① 企业信息</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">AI 会据此生成行业专属画像与合规约束。</div>
        </div>
        <el-form :model="form" label-width="120px" style="max-width: 640px">
          <el-form-item label="企业名称" required>
            <el-input v-model="form.name" placeholder="例如：XX 皮肤管理中心（XX路店）" />
          </el-form-item>
          <el-form-item label="所在行业">
            <el-select v-model="form.industry">
              <el-option label="生美（Beauty Local）" value="beauty_local" />
            </el-select>
          </el-form-item>
          <el-form-item label="License 编号">
            <el-input v-model="form.license" placeholder="《卫生许可证》编号（用于 Fact 校验）" />
          </el-form-item>
          <el-form-item label="联系人"><el-input v-model="form.contact_name" /></el-form-item>
          <el-form-item label="联系电话"><el-input v-model="form.contact_phone" /></el-form-item>
          <el-form-item label="门店地址">
            <el-input v-model="form.address" placeholder="用于 AI 生成「附近推荐」类回答" />
          </el-form-item>
        </el-form>
      </template>

      <template v-else-if="store.currentStep === 1">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">② 知识种子 Fact</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">先写入 3-5 条不可动摇的事实。AI 所有生成内容都会追溯到这些 Fact。</div>
        </div>
        <div v-for="(f, i) in seedFacts" :key="i" style="margin-bottom:12px">
          <el-input v-model="f.title" placeholder="Fact 标题，例如「敏感肌修护成分」" style="margin-bottom:6px" />
          <el-input v-model="f.content" type="textarea" :rows="2" placeholder="具体事实描述（用于 fact_refs 追溯）" />
        </div>
        <el-button plain @click="seedFacts.push({title:'',content:''})">+ 再加一条 Fact</el-button>
      </template>

      <template v-else-if="store.currentStep === 2">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">③ 用户画像（草稿预览）</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">S4 阶段将由 DIAGNOSE→PERSONA LangGraph 子图基于种子 Fact 生成。</div>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="核心人群">25-45 岁城市女性，中高收入</el-descriptions-item>
          <el-descriptions-item label="典型地域">XX 区 3km 范围，白领/宝妈为主</el-descriptions-item>
          <el-descriptions-item label="核心诉求" :span="2">补水 / 抗衰 / 敏感肌修护 / 祛痘</el-descriptions-item>
          <el-descriptions-item label="决策因子" :span="2">口碑 > 资质 > 距离 > 价格 > 装修</el-descriptions-item>
          <el-descriptions-item label="AI 典型问法" :span="2">
            <el-tag v-for="q in sampleQueries" :key="q" style="margin: 3px 4px">{{ q }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </template>

      <template v-else-if="store.currentStep === 3">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">④ 竞品分析（草稿预览）</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">S4 将从 AI 提及中抓取竞品，输出差异化机会点。</div>
        </div>
        <el-table :data="competitors" border stripe>
          <el-table-column prop="name" label="竞品" />
          <el-table-column prop="type" label="类型" width="110" />
          <el-table-column label="AI 提及率" width="140">
            <template #default="{ row }">
              <el-progress :percentage="row.rate" :stroke-width="10" />
            </template>
          </el-table-column>
          <el-table-column prop="gap" label="我们的差异化" min-width="280" />
        </el-table>
      </template>

      <template v-else-if="store.currentStep === 4">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">⑤ Scenario 场景挖掘（MVP-A 首轮 2 个）</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">每个 Scenario = 一个真实问答场景，后续内容生产的最小单元。</div>
        </div>
        <el-table :data="scenarios" border stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="query" label="用户问题" min-width="320" />
          <el-table-column prop="intent" label="意图" width="130">
            <template #default="{ row }"><el-tag size="small">{{ row.intent }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="channel" label="渠道/引擎" width="140" />
          <el-table-column prop="skill" label="Skill" width="110" />
          <el-table-column prop="priority" label="优先级" width="90" align="center" />
        </el-table>
      </template>

      <template v-else-if="store.currentStep === 5">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">⑥ 渠道权重</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">托管页 AUTO → 小红书/知乎 SEMI → 点评 GUIDED。</div>
        </div>
        <div v-for="(c, i) in channels" :key="c.name" style="margin-bottom: 18px">
          <div style="display:flex; justify-content:space-between; margin-bottom: 8px">
            <div>
              <b>{{ c.name }}</b>
              <el-tag size="small" :type="c.mode==='auto'?'success':c.mode==='semi'?'warning':'info'" style="margin-left:8px">
                {{ c.mode.toUpperCase() }}
              </el-tag>
            </div>
            <span style="color:#409eff; font-weight:600">{{ weights[i] }}%</span>
          </div>
          <el-slider v-model="weights[i]" :min="0" :max="100" :step="5" />
        </div>
        <div style="color:#909399; font-size:12px">合计：{{ weights.reduce((s, v) => s + v, 0) }}%</div>
      </template>

      <template v-else-if="store.currentStep === 6">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">⑦ 方案包确认（人工闸门 1/2）</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">确认后作为生产与监测基准，不可随意变更。</div>
        </div>
        <el-alert type="warning" show-icon :closable="false" style="margin-bottom:14px">
          <template #title>双人工闸门原则</template>
          方案包确认 → 草稿人工审。两次确认之间 AI 无法直接发布。
        </el-alert>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="核心 Scenario">{{ scenarios.length }} 个（MVP-A 首轮）</el-descriptions-item>
          <el-descriptions-item label="覆盖引擎">豆包 / DeepSeek / Kimi / 文心</el-descriptions-item>
          <el-descriptions-item label="首轮 SKU">FAQ × 1 + 小红书 × 1</el-descriptions-item>
          <el-descriptions-item label="发布模式">托管页 AUTO + 小红书 SEMI</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top:18px">
          <el-checkbox v-model="confirmed1">我已核对方案包内容，确认作为基准</el-checkbox>
        </div>
      </template>

      <template v-else>
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">⑧ 首轮内容出稿</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">AI 基于 Scenario 生成内容 → 机器审 → 草稿工作台 → 人工闸门 2/2。</div>
        </div>
        <el-steps :active="2" finish-status="success" align-center simple style="margin: 18px 0">
          <el-step title="kb_fetch" />
          <el-step title="LLM 生成" />
          <el-step title="fact_verify" />
          <el-step title="合规审核" />
          <el-step title="草稿工作台" />
        </el-steps>
        <el-empty description="S4 阶段实现生产子图（GAP→PLAN→EXECUTE→机器审）">
          <template #extra>
            <el-button type="primary" :disabled="!confirmed1" @click="$router.push('/content/drafts')">前往草稿工作台</el-button>
          </template>
        </el-empty>
      </template>
    </div>

    <div style="display:flex; justify-content:space-between; margin-top: 14px">
      <el-button :disabled="!store.canPrev" @click="store.prev()">上一步</el-button>
      <div>
        <el-button v-if="store.currentStep === 6" type="warning" :disabled="!confirmed1" @click="onConfirmPack">
          ⚠️ 确认方案包（人工闸门 1/2）
        </el-button>
        <el-button v-if="store.currentStep < 7" type="primary" @click="store.next()">下一步</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import ProgressChain, { type ChainStep } from '@/components/ProgressChain.vue'
import { useOnboardingStore } from '@/stores/onboarding'
import { runOnboarding, getOnboardingStatus } from '@/api/onboarding'

defineProps<{ steps?: ChainStep[] }>()

const router = useRouter()
const store = useOnboardingStore()

const form = reactive({
  name: 'XX 皮肤管理中心（XX路店）',
  industry: 'beauty_local',
  license: '',
  contact_name: 'Demo User',
  contact_phone: '',
  address: 'XX 市 XX 区 XX 路 88 号 2F',
})

const seedFacts = ref([
  { title: '门店资质', content: '本机构持有《卫生许可证》与《营业执照》，美容师均持资格证上岗。' },
  { title: '敏感肌项目说明', content: '敏感肌修护采用 XXX 植物萃取，经斑贴测试 0 过敏率。' },
  { title: '地址与营业时间', content: form.address + '，营业时间 10:00-21:30，全年无休。' },
])

const sampleQueries = [
  '敏感肌泛红去哪里做护理比较好？',
  '夏天油皮补水美容院推荐',
  'XX 区附近做抗衰的美容院',
]

const competitors = ref([
  { name: '连锁品牌A', type: '连锁', rate: 42, gap: '我们更本地、更深度服务，客制化方案' },
  { name: '附近门店B', type: '本地', rate: 18, gap: '资质齐全 + 明确成分清单' },
  { name: '工作室C', type: '工作室', rate: 5, gap: '卫生透明 + 正规发票' },
])

const scenarios = ref([
  { id: 1, query: 'XX区做敏感肌修护推荐哪家美容院？', intent: '到店决策', channel: '豆包/托管页', skill: 'faq', priority: 1 },
  { id: 2, query: '夏天油皮补水美容院做什么项目比较好？', intent: '项目咨询', channel: '小红书 SEMI', skill: 'article', priority: 2 },
])

const channels = [
  { name: 'AI 托管页', mode: 'auto' },
  { name: '小红书', mode: 'semi' },
  { name: '知乎', mode: 'semi' },
  { name: '大众点评', mode: 'guided' },
  { name: '抖音', mode: 'guided' },
]
const weights = ref([40, 25, 15, 15, 5])

const confirmed1 = ref(false)

function onStepChange(i: number) {
  if (store.status === 'running') return
  store.setStep(i)
}

async function start() {
  try {
    const data = await runOnboarding({ industry: form.industry, mode: 'quick' })
    store.setStatus('running', { taskId: data.data?.task_id || 'task_' + Date.now(), progress: 0, message: '开始执行 Agent...' })
    ElMessage.success(data.message || '已启动向导任务')
    await pollStatus()
  } catch (e) {
    store.setStatus('idle')
  }
}

async function pollStatus() {
  const taskId = store.taskId
  if (!taskId) return
  let round = 0
  while (round < 30) {
    round++
    try {
      const res = await getOnboardingStatus(taskId)
      const s = res.data
      if (s) {
        store.setStatus(s.status, { progress: s.progress_pct, message: s.progress_message })
        if (s.status === 'done' && s.step != null) store.setStep(Math.min(s.step, store.steps.length - 1))
        if (s.status === 'done' || s.status === 'failed') break
      }
    } catch {}
    await new Promise((r) => setTimeout(r, 1200))
  }
}

async function onConfirmPack() {
  try {
    await ElMessageBox.confirm('确认后将生成本次方案包基准，进入生产环节，是否继续？', '二次确认', {
      type: 'warning',
      confirmButtonText: '确认方案包',
    })
    ElMessage.success('方案包已确认，跳转内容草稿…')
    setTimeout(() => router.push('/content/drafts'), 600)
  } catch {}
}

watch(
  () => form.address,
  (v) => (seedFacts.value[2].content = v + '，营业时间 10:00-21:30，全年无休。'),
)
</script>
