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
        <el-button plain @click="onReset" :disabled="store.status==='running'">重新开始</el-button>
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
          <el-divider content-position="left">品牌</el-divider>
          <el-form-item label="品牌名称">
            <el-input v-model="brandForm.name" placeholder="默认与企业名称相同" />
          </el-form-item>
          <el-form-item label="差异化描述">
            <el-input v-model="brandForm.differentiator" type="textarea" :rows="2" placeholder="相对竞品的差异点" />
          </el-form-item>
          <el-form-item label="品牌 Slogan">
            <el-input v-model="brandForm.slogan" placeholder="一句话品牌主张" />
          </el-form-item>
          <el-divider content-position="left">门店 / 引擎</el-divider>
          <el-form-item label="城市">
            <el-input v-model="storeForm.city" placeholder="例如：上海" />
          </el-form-item>
          <el-form-item label="商圈/区">
            <el-input v-model="storeForm.district" placeholder="例如：静安区 / 静安寺" />
          </el-form-item>
          <el-form-item label="营业时间">
            <el-input v-model="storeForm.business_hours" placeholder="例如：10:00-21:30" />
          </el-form-item>
          <el-form-item label="主攻 AI 引擎">
            <el-select v-model="selectedEngines" multiple placeholder="选择目标引擎" style="width:100%">
              <el-option label="豆包" value="doubao" />
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="Kimi" value="kimi" />
              <el-option label="文心" value="wenxin" />
            </el-select>
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

        <el-divider content-position="left">服务项目</el-divider>
        <div v-for="(s, i) in serviceList" :key="'svc-'+i" style="margin-bottom:14px;padding:12px;border:1px solid #ebeef5;border-radius:6px">
          <el-form label-width="90px">
            <el-form-item label="项目名称">
              <el-input v-model="s.name" placeholder="例如：敏感肌修护" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="s.description" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="分类">
              <el-input v-model="s.category" placeholder="例如：护理 / 抗衰" />
            </el-form-item>
            <el-form-item label="价格提示">
              <el-input v-model="s.price_hint" placeholder="例如：398 起" />
            </el-form-item>
          </el-form>
          <el-button v-if="serviceList.length > 1" text type="danger" @click="serviceList.splice(i, 1)">删除</el-button>
        </div>
        <el-button plain @click="serviceList.push({ name: '', description: '', category: '', price_hint: '' })">+ 再加一项服务</el-button>
      </template>

      <template v-else-if="store.currentStep === 2">
        <div style="margin-bottom:18px">
          <h3 style="margin:0;font-size:16px">③ 用户画像</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">填写目标客群与自由补充；DIAGNOSE→PERSONA 会据此生成画像。</div>
        </div>
        <el-form label-width="120px" style="max-width: 640px; margin-bottom: 18px">
          <el-form-item label="目标客群">
            <el-input
              v-model="targetCustomers"
              type="textarea"
              :rows="3"
              placeholder="例如：25-45 岁城市女性，中高收入，敏感肌/抗衰需求"
            />
          </el-form-item>
          <el-form-item label="自由输入">
            <el-input
              v-model="rawInputs"
              type="textarea"
              :rows="4"
              placeholder="想对 AI 说的任何补充信息（会写入 Enterprise.raw_inputs，供词库汇聚）"
            />
          </el-form-item>
        </el-form>
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
          <h3 style="margin:0;font-size:16px">④ 竞品分析</h3>
          <div style="color:#909399;font-size:13px;margin-top:4px">先填已知竞品名称（一行一个）；S4 将从 AI 提及中补充差异化机会点。</div>
        </div>
        <el-form label-width="120px" style="max-width: 640px; margin-bottom: 18px">
          <el-form-item label="已知竞品">
            <el-input
              v-model="competitorsText"
              type="textarea"
              :rows="4"
              placeholder="一行一个竞品名称"
            />
          </el-form-item>
        </el-form>
        <el-table :data="competitorsPreview" border stripe>
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
          <el-descriptions-item label="覆盖引擎">{{ selectedEngines.join(' / ') || '未选择' }}</el-descriptions-item>
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
import { ref, reactive, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import ProgressChain, { type ChainStep } from '@/components/ProgressChain.vue'
import { useOnboardingStore } from '@/stores/onboarding'
import {
  runOnboarding,
  subscribeOnboardingEvents,
  type OnboardingRunRequest,
} from '@/api/onboarding'

defineProps<{ steps?: ChainStep[] }>()

const router = useRouter()
const store = useOnboardingStore()

const fd = store.formData
const primaryStore = fd.stores[0] || {
  name: '',
  city: '',
  district: '',
  address: '',
  phone: '',
  business_hours: '10:00-21:30',
}

const form = reactive({
  name: fd.enterprise.name,
  industry: fd.enterprise.industry || 'beauty_local',
  license: fd.enterprise.license_no,
  contact_name: fd.enterprise.contact_name,
  contact_phone: fd.enterprise.contact_phone,
  address: primaryStore.address,
})

const brandForm = reactive({
  name: fd.brand.name,
  differentiator: fd.brand.differentiator,
  slogan: fd.brand.slogan,
})

const storeForm = reactive({
  city: primaryStore.city,
  district: primaryStore.district,
  business_hours: primaryStore.business_hours || '10:00-21:30',
})

const selectedEngines = ref<string[]>([...(fd.target_engines || ['doubao'])])
const seedFacts = ref(fd.seed_facts.map((f) => ({ ...f })))
const serviceList = ref(
  (fd.services.length ? fd.services : [{ name: '', description: '', category: '', price_hint: '' }]).map(
    (s) => ({ ...s }),
  ),
)
const targetCustomers = ref(fd.target_customers || '')
const rawInputs = ref(fd.raw_inputs || '')
const competitorsText = ref((fd.competitors || []).join('\n'))

const sampleQueries = [
  '敏感肌泛红去哪里做护理比较好？',
  '夏天油皮补水美容院推荐',
  'XX 区附近做抗衰的美容院',
]

const competitorsPreview = ref([
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

let es: EventSource | null = null

function syncFormDataToStore() {
  store.formData.enterprise = {
    name: form.name,
    industry: form.industry,
    license_no: form.license,
    contact_name: form.contact_name,
    contact_phone: form.contact_phone,
  }
  store.formData.brand = {
    name: brandForm.name,
    differentiator: brandForm.differentiator,
    slogan: brandForm.slogan,
  }
  store.formData.stores = [
    {
      name: form.name,
      city: storeForm.city,
      district: storeForm.district,
      address: form.address,
      phone: form.contact_phone,
      business_hours: storeForm.business_hours,
    },
  ]
  store.formData.services = serviceList.value.map((s) => ({ ...s }))
  store.formData.competitors = competitorsText.value
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)
  store.formData.target_customers = targetCustomers.value
  store.formData.raw_inputs = rawInputs.value
  store.formData.seed_facts = seedFacts.value.map((f) => ({ ...f }))
  store.formData.target_engines = [...selectedEngines.value]
}

function onStepChange(i: number) {
  if (store.status === 'running') return
  syncFormDataToStore()
  store.setStep(i)
}

function onReset() {
  es?.close()
  es = null
  store.reset()
}

async function start() {
  syncFormDataToStore()

  if (!form.name?.trim()) {
    ElMessage.warning('请填写企业名称')
    return
  }

  const body: OnboardingRunRequest = {
    enterprise: {
      name: form.name,
      industry: form.industry,
      license_no: form.license,
      contact_name: form.contact_name,
      contact_phone: form.contact_phone,
    },
    brand: {
      name: brandForm.name || form.name,
      differentiator: brandForm.differentiator,
      slogan: brandForm.slogan,
    },
    stores: [
      {
        name: form.name,
        city: storeForm.city,
        district: storeForm.district,
        address: form.address,
        phone: form.contact_phone,
        business_hours: storeForm.business_hours,
        is_primary: true,
      },
    ],
    services: serviceList.value
      .filter((s) => s.name?.trim())
      .map((s) => ({
        name: s.name,
        description: s.description,
        category: s.category,
        price_hint: s.price_hint,
      })),
    competitors: competitorsText.value
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean),
    target_customers: targetCustomers.value,
    raw_inputs: rawInputs.value,
    seed_facts: seedFacts.value.filter((f) => f.title && f.content),
    target_engines: selectedEngines.value,
    search_enabled: true,
  }

  try {
    store.setStatus('running', { progress: 0, message: '正在提交入驻数据…' })
    const res: any = await runOnboarding(body)
    // AgentTaskResponse 直接返回（无 data 信封）；兼容 data.task_id
    const taskId = res?.data?.task_id ?? res?.task_id ?? res?.data?.id ?? res?.id
    if (!taskId) throw new Error('未返回 task_id')

    store.taskId = taskId

    es?.close()
    es = subscribeOnboardingEvents(taskId)
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const rawStatus = String(data.status || 'running')
        const mapped =
          rawStatus === 'completed' || rawStatus === 'done'
            ? 'done'
            : rawStatus === 'failed'
              ? 'failed'
              : 'running'
        store.setStatus(mapped, {
          progress: Number(data.progress_pct) || 0,
          message: data.progress_message || '',
        })
        if (mapped === 'done') {
          es?.close()
          es = null
          ElMessage.success('入驻完成！')
          setTimeout(() => router.push('/outcomes'), 1000)
        } else if (mapped === 'failed') {
          es?.close()
          es = null
          ElMessage.error(data.progress_message || '入驻失败')
        }
      } catch {
        /* ignore malformed SSE chunk */
      }
    }
    es.onerror = () => {
      es?.close()
      es = null
      if (store.status === 'running') {
        store.setStatus('failed', { message: 'SSE 连接中断' })
      }
    }
  } catch (e: any) {
    store.setStatus('idle')
    ElMessage.error(e?.response?.data?.detail || e?.message || '提交失败')
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
  (v) => {
    if (seedFacts.value[2]) {
      seedFacts.value[2].content =
        v + `，营业时间 ${storeForm.business_hours || '10:00-21:30'}，全年无休。`
    }
  },
)

watch(
  [form, brandForm, storeForm, selectedEngines, seedFacts, serviceList, targetCustomers, rawInputs, competitorsText],
  () => syncFormDataToStore(),
  { deep: true },
)

onBeforeUnmount(() => {
  es?.close()
  es = null
})
</script>
