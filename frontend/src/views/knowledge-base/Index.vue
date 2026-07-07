<template>
  <div>
    <div class="page-header">
      <div>
        <h2>📚 知识库 KB</h2>
        <div class="subtitle">Fact / FAQ / Signal / External · 三层可追溯</div>
      </div>
      <div>
        <el-upload action="" :auto-upload="false" :show-file-list="false">
          <el-button>📤 批量导入</el-button>
        </el-upload>
        <el-button type="primary" @click="openFactDialog">+ 新增 Fact</el-button>
      </div>
    </div>

    <div class="page-card" style="padding: 0">
      <el-tabs v-model="tab">
        <el-tab-pane label="Fact 事实库" name="fact">
          <el-table :data="facts" border stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="content" label="内容" min-width="320" show-overflow-tooltip />
            <el-table-column prop="category" label="分类" width="120">
              <template #default="{ row }">
                <el-tag size="small" plain>{{ row.category }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="verified" label="已校验" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.verified" size="small" type="success">已校验</el-tag>
                <el-tag v-else size="small" type="info">待校验</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default>
                <el-button link type="primary" size="small">编辑</el-button>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="FAQ 问答" name="faq">
          <el-table :data="faqs" border stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="question" label="问题" min-width="240" />
            <el-table-column prop="answer" label="回答" min-width="360" show-overflow-tooltip />
            <el-table-column prop="verified" label="已校验" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.verified" size="small" type="success">已校验</el-tag>
                <el-tag v-else size="small" type="info">待校验</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Fact 引用" width="120">
              <template #default="{ row }">{{ row.refs }}</template>
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
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
const tab = ref('fact')
const facts = [
  { id: 1, title: '门店资质', content: '本机构持有《卫生许可证》与《营业执照》，所有美容师持美容师职业资格证上岗。', category: '资质', verified: true },
  { id: 2, title: '敏感肌项目说明', content: '敏感肌修护采用 XXX 植物萃取成分，经第三方斑贴测试 0 过敏率，适合泛红瘙痒肌肤。', category: '项目', verified: true },
  { id: 3, title: '地址与营业时间', content: 'XX 市 XX 区 XX 路 88 号 2F，营业时间 10:00-21:30，全年无休。', category: '联系', verified: true },
]
const faqs = [
  { id: 1, question: '敏感肌可以做补水项目吗？', answer: '可以，我们针对敏感肌有专用的修护补水流程……', verified: true, refs: 'Fact #1, #2' },
  { id: 2, question: '第一次到店有什么优惠？', answer: '新客可享首次体验 5 折，到店赠送皮肤检测一次。', verified: false, refs: '—' },
]
function openFactDialog() {
  ElMessage.success('S2 阶段实现：弹出 Fact 创建表单')
}
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

