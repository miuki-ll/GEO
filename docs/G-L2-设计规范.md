# DESIGN 视觉设计规范

> **版本**：v1.0 · 对齐 Element Plus | **日期**：2026-07-14  
> **关联**：`G-L2-架构设计说明书.md` · `PRD.md`

---

## 1. 全局视觉基调

### 1.1 整体风格

- **定位**：专业 SaaS 后台，简洁商务，不花哨
- **设计原则**：信息密度适中、操作路径短、卡片分区清晰
- **框架**：Element Plus（默认主题 + 少量覆写）

### 1.2 色值体系

| 用途 | 色值 | Tailwind / CSS |
|------|------|---------------|
| 主色调 | `#409EFF` | Element Plus 默认 primary |
| 成功色 | `#67C23A` | success |
| 警告色 | `#E6A23C` | warning |
| 危险色 | `#F56C6C` | danger |
| 信息色 | `#909399` | info |
| 背景灰 | `#F5F7FA` | 页面底色 |
| 卡片白 | `#FFFFFF` | 卡片/弹窗底 |
| 文字主色 | `#303133` | 标题/正文 |
| 文字辅色 | `#606266` | 次要信息 |
| 文字弱色 | `#909399` | 占位/禁用 |

**规则：** 不自定义色板，直接使用 Element Plus CSS 变量。需要品牌色区分时，通过 `--el-color-primary` 覆写。

### 1.3 字体规范

| 层级 | 字号 | 字重 | 行高 | Element Plus 对应 |
|------|------|------|------|------------------|
| 页面标题 H1 | 20px | 500 | 28px | el-page-header |
| 区块标题 H2 | 18px | 500 | 26px | — |
| 卡片标题 H3 | 16px | 500 | 24px | el-card header |
| 正文 | 14px | 400 | 22px | el-descriptions |
| 辅助文案 | 13px | 400 | 20px | el-tag / el-table secondary |
| 最小注脚 | 12px | 400 | 18px | 时间戳/统计口径 |

### 1.4 布局规则

| 属性 | 值 |
|------|-----|
| 页面最大宽度 | 1400px（居中，左右自适应 padding） |
| 卡片圆角 | `8px`（el-card 默认） |
| 表单宽度 | 标签 120px + 输入 400px（最大 100%） |
| 侧边栏宽 | 220px（折叠 64px） |
| 间距基准 | 8px 倍数：8/16/24/32px |

---

## 2. 全局通用组件

### 2.1 按钮

```html
<!-- 主操作 -->
<el-button type="primary">确认并生成草稿</el-button>

<!-- 次要操作 -->
<el-button>取消</el-button>

<!-- 危险操作 -->
<el-button type="danger">批量拒绝</el-button>

<!-- 文字按钮（表格内） -->
<el-button type="primary" link>通过</el-button>
```

**规则：**
- 每行最多 1 个主按钮
- 确认类操作前置 `ElMessageBox.confirm`
- 异步操作带 `loading` 状态

### 2.2 输入框

- 使用 `el-input` + `el-form-item` 绑定
- 必填项必加 `prop` + rules 校验
- 错误态由 `el-form` 自动处理

### 2.3 卡片

```html
<el-card shadow="never">
  <template #header>区块标题</template>
  内容
</el-card>
```

### 2.4 表格

```html
<el-table :data="list" v-loading="loading" stripe border>
  <el-table-column prop="title" label="标题" min-width="200" />
  <el-table-column label="操作" width="180">
    <template #default="{ row }">
      <el-button link type="primary" @click="approve(row)">通过</el-button>
      <el-button link type="danger" @click="reject(row)">打回</el-button>
    </template>
  </el-table-column>
</el-table>
```

### 2.5 弹窗

- 简单确认用 `ElMessageBox.confirm`
- 复杂表单用 `el-dialog`，宽度 ≤ 600px
- 发布步骤指引用 `el-drawer`

### 2.6 进度 / 标签

- 状态标签统一用 `el-tag`：`success`=已发布 `warning`=待审 `danger`=打回 `info`=草稿
- 进度用 `el-progress`：开店向导 job 链百分比

---

## 3. 页面状态（强制统一）

### 3.1 加载中

- 页面级：`v-loading` 骨架 + `el-skeleton` 三行占位
- 卡片级：`v-loading` 属性
- 按钮级：`:loading="submitting"`

### 3.2 空数据

```html
<el-empty description="暂无数据">
  <el-button type="primary">创建第一个</el-button>
</el-empty>
```

### 3.3 报错异常

```html
<el-result icon="error" title="加载失败" sub-title="请检查网络后重试">
  <template #extra>
    <el-button type="primary" @click="retry">重试</el-button>
  </template>
</el-result>
```

### 3.4 无权限 / 404

- 401 → 跳转登录页
- 403 → `el-result icon="warning" title="无权访问此页面"`
- 404 → `el-result icon="warning" title="页面不存在"`

---

## 4. 关键交互动效

| 场景 | 实现 |
|------|------|
| 页面切换 | `<transition name="fade" mode="out-in">` → opacity 0.2s |
| 卡片 hover | `el-card` 默认 shadow 变化 |
| 弹窗进出 | `el-dialog` 默认动画 |
| 列表加载 | `el-table v-loading` 内置骨架 |
| 进度更新 | SSE → `el-progress` 百分比 |

**不做：** 自定义复杂动画、过场特效。使用 Element Plus 内置过渡即可。

---

## 5. 三舱专属规范

### 5.1 舱1 · 开店向导

- 分步表单（`el-steps` + `el-form`）
- 步骤：选 AI → 店信息 → 目标客户 → 竞品 → 核心优势 → 素材
- 提交后显示 `el-progress` + ETA 提示 + 步骤节点状态

### 5.2 舱2 · 方案包

- 一页五区，竖向排列
- A/B/C/D 区为卡片，E 区折叠
- scenario 勾选用 `el-checkbox-group`
- 信息密度高，用 `el-descriptions` + `el-tag` 紧凑展示

### 5.3 舱3 · 效果舱

- Dashboard 布局：`el-row` + `el-col`，顶行为 KPI 卡片（4 个 `el-statistic`）
- 趋势图用 `v-chart`（ECharts）
- 临界告警用 `el-alert type="warning"`

---

## 6. 交互约束

1. **所有页面必须使用 Element Plus 组件**，禁止裸 HTML + 自写 CSS 替代已有组件
2. **新增组件先查 `element-plus` 官方文档**，确认不存在才自定义
3. **颜色统一用 Element Plus CSS 变量**（`var(--el-color-primary)`），不写死 HEX
4. **状态标签用 `el-tag`**，不要自定义 class 替代
5. **表单项 100% 绑定 `el-form-item`**，校验规则统一在 `rules` 中声明

---

*DESIGN v1.0 · Element Plus 原生规范 · 不额外造轮子*
