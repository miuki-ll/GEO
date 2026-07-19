<template>
  <div>
    <div class="page-header">
      <div>
        <h2>📚 知识库 KB</h2>
        <div class="subtitle">Fact / FAQ / Signal / External / 词库 · 三层可追溯</div>
      </div>
      <div style="display:flex; gap:10px">
        <el-upload action="" :auto-upload="false" :show-file-list="false">
          <el-button>📤 批量导入</el-button>
        </el-upload>
        <el-button v-if="tab === 'fact'" type="primary" @click="openFactDialog()">+ 新增 Fact</el-button>
        <el-button v-else-if="tab === 'faq'" type="primary" @click="openFaqDialog()">+ 新增 FAQ</el-button>
        <el-button v-else-if="tab === 'keywords'" type="primary" @click="openKeywordDialog()">+ 手动添加词</el-button>
      </div>
    </div>

    <div class="page-card" style="padding: 0">
      <el-tabs v-model="tab">
        <el-tab-pane label="Fact 事实库" name="fact">
          <el-table :data="facts" border stripe v-loading="factLoading">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="content" label="内容" min-width="320" show-overflow-tooltip />
            <el-table-column prop="category" label="分类" width="120">
              <template #default="{ row }">
                <el-tag size="small" plain>{{ row.category || '—' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="verified" label="已校验" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.verified" size="small" type="success">已校验</el-tag>
                <el-tag v-else size="small" type="info">待校验</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openFactDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="removeFact(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="FAQ 问答" name="faq">
          <el-table :data="faqs" border stripe v-loading="faqLoading">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="question" label="问题" min-width="240" />
            <el-table-column prop="answer" label="回答" min-width="360" show-overflow-tooltip />
            <el-table-column prop="verified" label="已校验" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.verified" size="small" type="success">已校验</el-tag>
                <el-tag v-else size="small" type="info">待校验</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="fact_refs" label="Fact 引用" width="140">
              <template #default="{ row }">
                {{ (row.fact_refs || []).length ? (row.fact_refs as number[]).map((id: number) => `#${id}`).join(', ') : '—' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openFaqDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="removeFaq(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="Signal 信号" name="signal">
          <div class="empty-tip">
            <el-empty description="L3 阶段将自动从外部/交互中捕捉 kb_signals" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="External 外部信源" name="external">
          <div class="empty-tip">
            <el-empty description="S2 阶段实现 URL 抓取、外部内容入库" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="词库" name="keywords">
          <div style="margin-bottom:12px; display:flex; gap:8px; align-items:center; flex-wrap:wrap">
            <el-button type="primary" @click="triggerGenerate" :loading="generating">
              🤖 生成词库
            </el-button>
            <el-button plain @click="openKeywordDialog()">+ 手动添加</el-button>
            <el-select v-model="keywordFilter.layer" placeholder="层级筛选" clearable style="width:120px" @change="onKwFilterChange">
              <el-option v-for="l in ['认知层','选型层','痛点层','场景层']" :key="l" :label="l" :value="l" />
            </el-select>
            <el-select v-model="keywordFilter.source" placeholder="来源筛选" clearable style="width:130px" @change="onKwFilterChange">
              <el-option v-for="s in ['RawInputs','探针反推','SEO API','LLM生成','手动']" :key="s" :label="s" :value="s" />
            </el-select>
            <el-input v-model="keywordFilter.search" placeholder="搜索关键词" clearable style="width:200px" @change="onKwFilterChange" />
          </div>
          <el-table :data="keywords" border stripe v-loading="kwLoading">
            <el-table-column prop="phrase" label="关键词" min-width="200" />
            <el-table-column prop="layer" label="层级" width="100">
              <template #default="{ row }">
                <el-tag :type="layerType(row.layer)" size="small">{{ row.layer || '未分类' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="110">
              <template #default="{ row }">
                <el-tag size="small" plain>{{ row.source }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="lbs_tags" label="LBS标签" width="150">
              <template #default="{ row }">
                <el-tag v-for="t in (row.lbs_tags || [])" :key="t" size="small" style="margin:2px">{{ t }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openKeywordDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="removeKeyword(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:12px; text-align:right">
            <el-pagination
              v-model:current-page="kwPage"
              :page-size="kwPageSize"
              :total="kwTotal"
              layout="prev, pager, next"
              @current-change="loadKeywords"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Fact 弹窗 -->
    <el-dialog v-model="factDialogVisible" :title="editingFactId ? '编辑 Fact' : '新增 Fact'" width="560px">
      <el-form :model="factForm" label-width="90px">
        <el-form-item label="标题" required>
          <el-input v-model="factForm.title" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="factForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="factForm.category" />
        </el-form-item>
        <el-form-item label="来源类型">
          <el-input v-model="factForm.source_type" placeholder="manual" />
        </el-form-item>
        <el-form-item label="已校验">
          <el-switch v-model="factForm.verified" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="factDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFact">保存</el-button>
      </template>
    </el-dialog>

    <!-- FAQ 弹窗 -->
    <el-dialog v-model="faqDialogVisible" :title="editingFaqId ? '编辑 FAQ' : '新增 FAQ'" width="560px">
      <el-form :model="faqForm" label-width="90px">
        <el-form-item label="问题" required>
          <el-input v-model="faqForm.question" />
        </el-form-item>
        <el-form-item label="回答" required>
          <el-input v-model="faqForm.answer" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="faqForm.category" />
        </el-form-item>
        <el-form-item label="已校验">
          <el-switch v-model="faqForm.verified" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="faqDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFaq">保存</el-button>
      </template>
    </el-dialog>

    <!-- Keyword 弹窗 -->
    <el-dialog v-model="kwDialogVisible" :title="editingKwId ? '编辑关键词' : '手动添加关键词'" width="520px">
      <el-form :model="kwForm" label-width="90px">
        <el-form-item label="关键词" required>
          <el-input v-model="kwForm.phrase" />
        </el-form-item>
        <el-form-item label="层级">
          <el-select v-model="kwForm.layer" clearable placeholder="选择层级" style="width:100%">
            <el-option v-for="l in ['认知层','选型层','痛点层','场景层']" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="kwForm.source" style="width:100%">
            <el-option v-for="s in ['RawInputs','探针反推','SEO API','LLM生成','手动']" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="LBS标签">
          <el-select
            v-model="kwForm.lbs_tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入后回车添加"
            style="width:100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="kwDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveKeyword">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listFacts,
  createFact,
  updateFact,
  deleteFact,
  listFaqs,
  createFaq,
  updateFaq,
  deleteFaq,
  listKeywords,
  createKeyword,
  updateKeyword,
  deleteKeyword,
  generateKeywords,
} from '@/api/kb'
import type { FactForm, FaqForm, KeywordItem, KeywordForm } from '@/api/kb'
import type { KBFactItem, KBFaqItem } from '@/types'

const tab = ref('fact')

function unwrapList<T>(res: any): T[] {
  if (Array.isArray(res?.items)) return res.items
  if (Array.isArray(res?.data?.items)) return res.data.items
  if (Array.isArray(res?.data)) return res.data
  return []
}

// ── Facts ──
const facts = ref<KBFactItem[]>([])
const factLoading = ref(false)
const factDialogVisible = ref(false)
const factForm = ref<FactForm>({
  title: '',
  content: '',
  source_type: 'manual',
  category: '',
  tags: [],
  verified: false,
})
const editingFactId = ref<number | null>(null)

async function loadFacts() {
  factLoading.value = true
  try {
    const res = await listFacts({ page_size: 100 })
    facts.value = unwrapList<KBFactItem>(res)
  } finally {
    factLoading.value = false
  }
}

function openFactDialog(fact?: KBFactItem) {
  if (fact) {
    editingFactId.value = fact.id
    factForm.value = {
      title: fact.title,
      content: fact.content,
      source_type: fact.source_type || 'manual',
      category: fact.category || '',
      tags: (fact as any).tags || [],
      verified: !!fact.verified,
    }
  } else {
    editingFactId.value = null
    factForm.value = {
      title: '',
      content: '',
      source_type: 'manual',
      category: '',
      tags: [],
      verified: false,
    }
  }
  factDialogVisible.value = true
}

async function saveFact() {
  try {
    if (editingFactId.value) {
      await updateFact(editingFactId.value, factForm.value)
      ElMessage.success('Fact 已更新')
    } else {
      await createFact(factForm.value)
      ElMessage.success('Fact 已创建')
    }
    factDialogVisible.value = false
    await loadFacts()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  }
}

async function removeFact(id: number) {
  try {
    await ElMessageBox.confirm('确定删除该 Fact？', '确认删除', { type: 'warning' })
    await deleteFact(id)
    ElMessage.success('已删除')
    await loadFacts()
  } catch {
    /* cancel */
  }
}

// ── FAQs ──
const faqs = ref<KBFaqItem[]>([])
const faqLoading = ref(false)
const faqDialogVisible = ref(false)
const faqForm = ref<FaqForm>({
  question: '',
  answer: '',
  category: '',
  tags: [],
  verified: false,
})
const editingFaqId = ref<number | null>(null)

async function loadFaqs() {
  faqLoading.value = true
  try {
    const res = await listFaqs({ page_size: 100 })
    faqs.value = unwrapList<KBFaqItem>(res)
  } finally {
    faqLoading.value = false
  }
}

function openFaqDialog(faq?: KBFaqItem) {
  if (faq) {
    editingFaqId.value = faq.id
    faqForm.value = {
      question: faq.question,
      answer: faq.answer,
      category: faq.category || '',
      tags: (faq as any).tags || [],
      fact_refs: faq.fact_refs || [],
      verified: !!faq.verified,
    }
  } else {
    editingFaqId.value = null
    faqForm.value = {
      question: '',
      answer: '',
      category: '',
      tags: [],
      verified: false,
    }
  }
  faqDialogVisible.value = true
}

async function saveFaq() {
  try {
    if (editingFaqId.value) {
      await updateFaq(editingFaqId.value, faqForm.value)
      ElMessage.success('FAQ 已更新')
    } else {
      await createFaq(faqForm.value)
      ElMessage.success('FAQ 已创建')
    }
    faqDialogVisible.value = false
    await loadFaqs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  }
}

async function removeFaq(id: number) {
  try {
    await ElMessageBox.confirm('确定删除该 FAQ？', '确认删除', { type: 'warning' })
    await deleteFaq(id)
    ElMessage.success('已删除')
    await loadFaqs()
  } catch {
    /* cancel */
  }
}

// ── Keywords ──
const keywords = ref<KeywordItem[]>([])
const kwLoading = ref(false)
const kwPage = ref(1)
const kwPageSize = ref(50)
const kwTotal = ref(0)
const generating = ref(false)
const keywordFilter = ref({ layer: '', source: '', search: '' })
const kwDialogVisible = ref(false)
const kwForm = ref<KeywordForm>({
  phrase: '',
  layer: '',
  source: '手动',
  lbs_tags: [],
  keyword_type: 'exact',
  pool_hint: 'core',
})
const editingKwId = ref<number | null>(null)

function layerType(layer: string) {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    认知层: '',
    选型层: 'success',
    痛点层: 'danger',
    场景层: 'warning',
  }
  return map[layer] || 'info'
}

function onKwFilterChange() {
  kwPage.value = 1
  loadKeywords()
}

async function loadKeywords() {
  kwLoading.value = true
  try {
    const res: any = await listKeywords({
      layer: keywordFilter.value.layer || undefined,
      source: keywordFilter.value.source || undefined,
      search: keywordFilter.value.search || undefined,
      page: kwPage.value,
      page_size: kwPageSize.value,
    })
    const payload = res?.data && (res.data.items || res.data.total != null) ? res.data : res
    keywords.value = payload?.items || []
    kwTotal.value = payload?.total || 0
  } finally {
    kwLoading.value = false
  }
}

function openKeywordDialog(kw?: KeywordItem) {
  if (kw) {
    editingKwId.value = kw.id
    kwForm.value = {
      phrase: kw.phrase,
      layer: kw.layer,
      source: kw.source,
      lbs_tags: kw.lbs_tags || [],
      keyword_type: kw.keyword_type,
      pool_hint: kw.pool_hint,
    }
  } else {
    editingKwId.value = null
    kwForm.value = {
      phrase: '',
      layer: '',
      source: '手动',
      lbs_tags: [],
      keyword_type: 'exact',
      pool_hint: 'core',
    }
  }
  kwDialogVisible.value = true
}

async function saveKeyword() {
  try {
    if (!kwForm.value.phrase?.trim()) {
      ElMessage.warning('请填写关键词')
      return
    }
    if (editingKwId.value) {
      await updateKeyword(editingKwId.value, kwForm.value)
    } else {
      await createKeyword(kwForm.value)
    }
    kwDialogVisible.value = false
    await loadKeywords()
    ElMessage.success('已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  }
}

async function removeKeyword(id: number) {
  try {
    await ElMessageBox.confirm('确定删除？', '确认', { type: 'warning' })
    await deleteKeyword(id)
    await loadKeywords()
    ElMessage.success('已删除')
  } catch {
    /* cancel */
  }
}

async function triggerGenerate() {
  generating.value = true
  try {
    const res: any = await generateKeywords()
    const taskId = res?.data?.task_id ?? res?.task_id
    ElMessage.success(`词库生成任务已启动（task #${taskId ?? '?'}），请稍后刷新查看`)
    setTimeout(() => {
      loadKeywords()
      generating.value = false
    }, 5000)
  } catch (e: any) {
    generating.value = false
    ElMessage.error(e?.response?.data?.detail || e?.message || '生成失败')
  }
}

watch(tab, (v) => {
  if (v === 'fact') loadFacts()
  else if (v === 'faq') loadFaqs()
  else if (v === 'keywords') loadKeywords()
})

onMounted(() => {
  loadFacts()
})
</script>

<style scoped>
:deep(.el-tabs__header) {
  padding: 0 20px;
  margin: 0;
}
:deep(.el-tabs__content) {
  padding: 20px;
}
</style>
