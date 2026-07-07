# GEO MVP-A · 7 天 Vibe Coding 开发计划

> **版本**：v1.0 | **日期**：2026-07-04  
> **目标**：1 店 demo — 开店向导 → 方案包（2 scenario）→ FAQ + 小红书 SEMI → 托管页 → 效果舱  
> **方式**：Cursor Agent 写代码，你验收 happy path  
> **关联**：`PRD-v4.md` · `GEO-架构设计说明书.md` · `GEO-实施清单.md`

---

## 本周范围（必砍）

| 完整 v4 | 本周 |
|---------|------|
| LangGraph + ReAct | Celery 线性 task 链 |
| 4 个 AI 引擎 | 只做 **豆包 doubao** |
| Faiss 聚类 | LLM 直接出 pain_clusters |
| SEO API | 砍掉 |
| 完整 RBAC | 单租户 + JWT 登录 |
| 小红书 AUTO | 直接 **SEMI 导出** |
| Core + Probe | 只做 Core 5 条 prompt |
| LangSmith / MCP | 留 `.env` 位，本周不接 |

---

## 每日目标总览（勾选完成情况）

| 天 | 日期 | 核心目标 | 完成 |
|:--:|------|----------|:----:|
| **D1** | __/__ | 项目能跑：docker + 登录 + 三舱空路由 + `/health` | ☐ |
| **D2** | __/__ | 舱1：6 步开店向导 + KB 写入 PG | ☐ |
| **D3** | __/__ | 舱1 后台：分析 job 链 + 进度条 + draft API | ☐ |
| **D4** | __/__ | 舱2：方案包 UI + confirm + 生成 FAQ/小红书草稿 | ☐ |
| **D5** | __/__ | 舱2→3：草稿三栏审 + 托管页 + 小红书 SEMI | ☐ |
| **D6** | __/__ | 舱3：Core 监测 + 效果舱 4 张卡片 | ☐ |
| **D7** | __/__ | 端到端联调 + demo 录屏无报错 | ☐ |

**周验收（D7 全勾才算完成）：**

- [ ] 开店向导 6 步提交成功
- [ ] 分析进度 0→100% 自动进方案包
- [ ] 勾选 2 scenario → confirm 出草稿
- [ ] FAQ + 小红书可审、批量通过
- [ ] 托管页 URL 可访问（含 JSON-LD）
- [ ] 小红书 SEMI 一键复制
- [ ] 效果舱：提及率 + 发布状态 + 托管页 PV
- [ ] fact_refs 可追溯；tenant 不串数据

---

## D1 · 脚手架 + 三舱空壳

### 目标

`docker compose up` → 浏览器登录 → 三舱页面可切换 → `GET /health` 200

### 任务

| # | 内容 | 验收 |
|---|------|------|
| 1.1 | monorepo 目录 + docker-compose | 一键启动 |
| 1.2 | PG 核心表 + Alembic 迁移 | migrate 成功 |
| 1.3 | JWT 登录（dev 固定 tenant） | 登录后进首页 |
| 1.4 | 三舱路由空页面 | 3 个 URL 可访问 |

### 给 AI 的提示词

**Prompt 1 — 工程骨架（上午）**

```
按 GEO v4 架构在仓库根目录初始化 monorepo：

目录：
- apps/web：Vue3 + Vite + TypeScript + Element Plus + Pinia
- apps/api：FastAPI + Pydantic v2 + SQLAlchemy + Alembic
- packages/llm：gateway 占位
- packages/industry/beauty_local：空目录
- infra/docker-compose.yml

docker-compose 服务：postgres、redis、api、web（dev 热重载）

数据库表（全部带 tenant_id）：
tenants, users, brands, stores, services, faqs, raw_inputs,
jobs, strategy_pack_drafts, content_assets, publish_tasks, monitor_runs

API：
- GET /health → { "status": "ok" }
- POST /auth/login → JWT
- dev 模式：登录后固定 tenant_id=1

约束：Python 3.11+，Pydantic v2，不要 LangGraph，不要 MCP。
README 写 docker compose up 三步启动。
```

**Prompt 2 — 三舱前端（下午）**

```
在 apps/web 实现：

路由：
- /login
- /onboarding（舱1，占位「开店向导」）
- /strategy-pack（舱2，占位「方案包」）
- /outcomes（舱3，占位「效果舱」）

布局：顶栏 + 三舱 Tab 导航；未登录跳 /login。
axios 封装：baseURL、JWT header、401 跳登录。
Pinia store：auth（token、tenantId）。

风格：卡片化、结论句大字号，Element Plus 默认主题即可。
```

### D1 完成标准

- [ ] `docker compose up` 无报错
- [ ] 登录后进三舱，切换正常
- [ ] `curl localhost:8000/health` 返回 ok

---

## D2 · 舱1 开店向导 + KB

### 目标

6 步表单填完 → 数据持久化 → `[开始分析]` 创建 job（进度 Day3 接）

### 任务

| # | 内容 | 验收 |
|---|------|------|
| 2.1 | KB CRUD API | brand/store/services/faqs/raw_inputs |
| 2.2 | 6 步向导 UI | 分步表单 + 校验 |
| 2.3 | onboarding/run | 写 KB + 创建 job(status=queued) |
| 2.4 | kb_updated_at | 任意 KB 变更刷新 |

### 给 AI 的提示词

**Prompt 1 — KB API**

```
在 apps/api 实现租户 KB CRUD（Pydantic v2 Request/Response）：

POST/GET/PUT /api/tenants/{tenant_id}/kb/brand
POST/GET/PUT /api/tenants/{tenant_id}/kb/stores
POST/GET/PUT /api/tenants/{tenant_id}/kb/services
POST/GET/POST /api/tenants/{tenant_id}/kb/faqs
POST/GET /api/tenants/{tenant_id}/kb/raw-inputs
POST/GET /api/tenants/{tenant_id}/kb/target-engines

所有查询必须 WHERE tenant_id = ?，跨 tenant 返回 403。
任意 Fact 写入刷新 tenants.kb_updated_at。
```

**Prompt 2 — 开店向导 UI + 提交**

```
实现 /onboarding 六步向导（Element Plus Steps + Form）：

Step1 TargetEngines：多选，默认勾选 doubao（主攻）
Step2 品牌/门店 NAP + 项目（≥2 个 service，含名称价格）
Step3 目标客户：模板多选（生美：新客/敏感肌/抗老等）
Step4 竞品 2 家：名称 + 可选链接
Step5 一句话核心优势
Step6 RawInputs：大文本框粘贴客服/评价

底部：[上一步] [下一步]；最后一步 [开始分析]

提交逻辑：
1. 逐步或最终批量调 KB API 写入
2. POST /api/tenants/{id}/onboarding/run → 返回 job_id
3. 跳转 /onboarding/progress?job_id=xxx（进度页 Day3 做）

表单校验：Step2 至少 1 门店 2 项目；Step4 至少 2 竞品。
```

### D2 完成标准

- [ ] 虚构店信息填完刷新仍在
- [ ] Network 可见 KB 各接口 200
- [ ] 点开始分析返回 job_id 并跳进度页

---

## D3 · 分析 job 链 + 方案包 draft

### 目标

进度条 0→100% → 自动跳方案包 → `GET strategy-pack/draft` 有 A～E JSON

### 任务

| # | 内容 | 验收 |
|---|------|------|
| 3.1 | Celery + Redis worker | worker 能消费 |
| 3.2 | 线性分析链 5 步 | diagnose→pain→persona→competitor→draft |
| 3.3 | SSE/轮询进度 | 前端进度条动 |
| 3.4 | doubao EngineAdapter | 至少 diagnose 调通 |

### 给 AI 的提示词

**Prompt 1 — Celery 分析链**

```
实现 apps/api/tasks/onboarding_chain.py（Celery chain，不要 LangGraph）：

1. source_diagnose：读 target_engines + KB，调 packages/llm/gateway doubao 联网 API，
   3 条 prompt，解析 citations → platform_stats JSON
2. pain_mine：LLM 读 raw_inputs → 5 个 pain_cluster，每项含 scenario 问法字符串
3. persona_analyze：LLM → buyer_personas[] + content_layout_plan[]
4. competitor_analyze：LLM 读竞品名 → differentiation_brief[]（不抓网页）
5. build_strategy_pack_draft：聚合为 StrategyPackDraft 写入 strategy_pack_drafts 表

jobs 表：step、progress(0-100)、status、error_message。
每步完成 progress += 20。

POST onboarding/run 触发 chain；GET onboarding/status/{job_id} 返回进度。
可选 SSE：GET onboarding/status/{job_id}/stream。
```

**Prompt 2 — 进度页 + draft API**

```
前端 /onboarding/progress：
- 读 job_id，轮询 status 每 2s（或 SSE）
- 展示：当前步骤中文名 + 进度条 + 预计文案（「正在测 AI 信源…」等）
- progress=100 → router.push('/strategy-pack?draft=1')

后端 GET /api/tenants/{id}/strategy-pack/draft：
返回 StrategyPackDraft Pydantic model：
- buyer_personas, content_layout_plan（A 区）
- differentiation_brief, competitor_topics（B 区）
- pain_clusters（C 区，带 id/scenario/selected 默认 false）
- source_weight_plan（D 区，scenario_slots 自动分配）
- keyword_library_draft, freshness（E 区）

LLM 慢时：支持读取 fixtures/beauty_analysis.json 降级（env USE_FIXTURES=true）。
```

### D3 完成标准

- [ ] 点开始分析后进度条走到 100%
- [ ] 自动跳转 /strategy-pack
- [ ] draft API 返回完整 JSON（浏览器 Network 可见）

---

## D4 · 方案包 UI + 内容生成

### 目标

勾选 2 scenario → confirm → 草稿 Tab 出现 FAQ + 1 篇小红书

### 任务

| # | 内容 | 验收 |
|---|------|------|
| 4.1 | 方案包 A+C 主界面 | 场景勾选 2 个 |
| 4.2 | thin KB 门槛 | 不足 FAQ 按钮禁用 |
| 4.3 | confirm → PLAN + EXECUTE | 出 content_assets |
| 4.4 | content_faq + beauty_xhs_note | kb_fetch → LLM |
| 4.5 | 机器审最小版 | fact_verify + 禁词 |

### 给 AI 的提示词

**Prompt 1 — 方案包 UI**

```
实现 /strategy-pack 页面（Tab：方案包 | 草稿）：

方案包 Tab 默认展示：
- A 画像卡片：primary persona 摘要 + content_layout_plan 要点
- C 场景列表：Checkbox，每项显示 scenario 问法，必选 2 个（min=2 max=5）
- [确认并生成草稿] 大按钮

折叠区「展开高级」：B 竞品 differentiation_brief 可编辑；D 渠道权重只读展示。

门槛：services<2 或 faqs<3 时按钮 disabled + 黄条「请补全 3 条 FAQ」。

确认调 POST /api/tenants/{id}/strategy-pack/confirm
body: StrategyPackConfirm（Pydantic extra=forbid）
- selected_scenario_ids（长度 2）
- selected_persona_ids, differentiation_brief, source_weight_plan
```

**Prompt 2 — 生成 + 机器审**

```
confirm 后 Orchestrator 简化版：

PLAN：2 scenario → 3 content_units
- 1× content_faq（托管页）
- 1× content_faq 或合并
- 1× beauty_xhs_note（channel=xiaohongshu, publish_mode=SEMI）

EXECUTE 每个 unit：
1. kb_fetch(fact_refs) 从 PG 取 Fact 文本
2. LLM 生成（packages/industry/beauty_local/prompts/）
3. 机器审：fact_verify（店名/价格在 KB 中存在）、compliance（banned_words.json）
4. 写入 content_assets（status=draft, fact_refs, review_result JSON）

GET /api/tenants/{id}/content-drafts 返回列表含 machine_review 告警。
confirm 完成后前端自动切到「草稿」Tab。
```

### D4 完成标准

- [ ] 勾选 2 场景后 confirm 成功
- [ ] 草稿 Tab ≥2 条（FAQ + 小红书）
- [ ] 机器审告警可见（有则红标）

---

## D5 · 草稿审 + 发布

### 目标

三栏审过 → 托管页可访问 → 小红书 SEMI 可复制

### 任务

| # | 内容 | 验收 |
|---|------|------|
| 5.1 | 草稿三栏工作台 | 预览/fact_refs/告警 |
| 5.2 | bulk-approve | draft → ready |
| 5.3 | 托管页 AUTO | HTML + FAQPage JSON-LD |
| 5.4 | 小红书 SEMI | 复制全文按钮 |

### 给 AI 的提示词

**Prompt 1 — 草稿审**

```
草稿 Tab 三栏布局：

左栏：Markdown 或 HTML 预览
中栏：fact_refs 列表，点击展示 KB 原文片段
右栏：machine_review 告警（通过绿/失败红）

底栏：[通过] [批量通过所选]
POST /api/tenants/{id}/content-drafts/bulk-approve
→ status=ready，写 approval_log（user_id, timestamp）
```

**Prompt 2 — 发布**

```
POST /api/publish-tasks body: { content_asset_ids: [...] }

HostedPageAdapter（AUTO）：
- 读 ready 的 content_faq
- 生成静态 HTML：品牌名、FAQ 列表、联系表单
- 注入 FAQPage JSON-LD（Schema 结构化数据）
- 路由 GET /p/{tenant_slug}/{page_id} 或存 MinIO
- 表单提交 → hosted_page_events（event=form_submit）
- publish_tasks.status=published, content_asset_id 必填

XhsAdapter（SEMI，不接真实 API）：
- 导出 title + body + tags
- publish_tasks.status=semi_exported
- 前端弹窗「复制全文」按钮

效果舱发布入口可先占位，Day6 聚合。
```

### D5 完成标准

- [ ] 批量通过后 status=ready
- [ ] 托管页 URL 浏览器可开
- [ ] 小红书稿一键复制成功

---

## D6 · 监测 + 效果舱

### 目标

手动触发 1 轮 Core 监测 → 效果舱 4 张卡片有真实数据

### 任务

| # | 内容 | 验收 |
|---|------|------|
| 6.1 | monitor_run（doubao） | 5 条 prompt |
| 6.2 | outcomes 聚合 API | AI+发布+托管页 |
| 6.3 | 效果舱 UI | 4 张报告卡片 |
| 6.4 | 手动「立即监测」按钮 | demo 用 |

### 给 AI 的提示词

**Prompt 1 — 监测**

```
实现 monitor：

setup：从 confirmed scenario（2 条）+ 品牌词（3 条）= 5 条 core_prompts
run：每条调 doubao 联网，检测回复是否含品牌名/店名
计算 mention_rate = 命中数 / 5
写入 monitor_runs（tenant_id, engine=doubao, mention_rate, details JSON）

POST /api/tenants/{id}/monitor/run 手动触发（demo 不依赖 Celery Beat）
GET /api/monitor/runs?tenant_id= 历史列表
```

**Prompt 2 — 效果舱**

```
GET /api/tenants/{id}/outcomes 聚合：

{
  ai_metrics: { mention_rate, engine: "doubao", last_run_at },
  hosted_page_stats: { pv, form_submits },
  publish_summary: [{ channel, status, content_asset_id, url? }],
  strategy_hints: ["提及率低可补充 FAQ"]  // 静态即可
}

前端 /outcomes 四卡片（大字号结论句）：
1. AI 可见度：「豆包 5 问中 X 次提到您」
2. 托管页：PV / 表单
3. 发布：托管页✅ 小红书📋
4. 策略提示 + [立即监测] 按钮

ready 资产可从此页一键 POST publish-tasks。
```

### D6 完成标准

- [ ] 点立即监测后有 mention_rate
- [ ] 效果舱 4 卡无空白
- [ ] 发布状态与 D5 一致

---

## D7 · 联调 + Demo

### 目标

完整路径跑通 3 遍，录 3 分钟 demo 无报错

### 任务

| # | 内容 | 验收 |
|---|------|------|
| 7.1 | 端到端冒烟 ×3 | 无 500 |
| 7.2 | 种子数据 fixture | 一键导入 dev |
| 7.3 | Loading/空状态/错误 toast | 体验可 demo |
| 7.4 | README + 录屏 | 交付 |

### 给 AI 的提示词

**Prompt 1 — 联调修复**

```
对照 MVP-A 验收跑端到端，修复所有阻断 bug：

路径：登录 → 开店向导 → 分析进度 → 方案包 confirm(2 scenario)
→ 草稿 bulk-approve → 发布托管页 → 复制小红书 → 效果舱监测

优先修：500 错误、进度卡住、confirm 无草稿、托管页 404、效果舱空。
tenant_id 隔离：用 tenant 2 访问 tenant 1 资源必须 403。
```

**Prompt 2 — Demo 种子 + 文档**

```
新增 scripts/seed_demo.py：
- 租户「美肌皮肤管理」完整 KB（2 项目、3 FAQ、raw_inputs、2 竞品）
- 可选跳过 LLM 写入预置 strategy_pack_draft + 草稿

更新 README：
- 环境变量说明（DOUBAO_API_KEY、USE_FIXTURES）
- Demo 三步：docker up → seed → 打开浏览器路径
- 3 分钟录屏脚本（逐步操作说明）
```

### D7 完成标准

- [ ] 周验收 8 项全勾
- [ ] 录屏一遍过
- [ ] README 他人可按说明复现

---

## 附录 A · 每日 Vibe Coding 节奏

| 时段 | 动作 |
|------|------|
| 前 30min | 读昨日代码，复制当日 Prompt |
| 中 4h | Agent 写 → 你跑 → 报错贴回修 |
| 后 1h | 点 happy path，记 bug |
| 最后 30min | commit，勾选上方总览表 |

## 附录 B · 卡住降级顺序

1. LLM 慢/贵 → `USE_FIXTURES=true` 读 JSON
2. Celery 不通 → FastAPI `BackgroundTasks` 同步
3. SSE 失败 → 2s 轮询
4. fact_verify 复杂 → 只查店名/价格是否在 KB 文本
5. 监测限流 → seed 一条 monitor_run

## 附录 C · Demo 录屏脚本（3 分钟）

```
0:00 登录
0:30 开店向导提交（或 seed 跳过）
1:00 看分析进度
1:30 方案包勾选 2 场景 → 确认生成
2:00 草稿审 → 批量通过
2:20 发布托管页 → 新 tab 打开
2:40 复制小红书
2:50 效果舱 → 立即监测 → 看提及率
```

---

*计划表 v1.0 — 完成请在文首总览表打勾 ☐→☑*
