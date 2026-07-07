# GEO 智能品牌平台 — 架构设计说明书

> **项目名称**：GEO 智能品牌平台  
> **文档版本**：V1.2  
> **编制日期**：2026-07-02  
> **地点**：广东  
> **关联文档**：GEO-需求规格说明书.md、GEO-概要设计说明书.md

---

## 1. 总体架构设计

系统采用 **「前后端分离 + AI 原生（AI-Native）」** 架构。核心创新：

1. **知识库驱动**：KB 为**对外发布事实的唯一权威**（Fact/Signal/External 分层）
2. **Agent + Skill**：Orchestrator 决策，Skill 执行（参考 MCP 思想）
3. **行业包可插拔**：`beauty_local` 等于应用层配置，平台内核不变
4. **分引擎可配置**：知识库 TargetEngines（客户选主攻/次攻）驱动诊断、策略、监测
5. **信源诊断先行**：发布前实测各 AI 引用来源，非静态渠道表

### 1.1 架构分层图

```
┌─────────────────────────────────────────────────────────────┐
│  展现层 Presentation                                         │
│  Vue 3 + Element Plus + Pinia                                │
│  页面：知识库 | 策略确认 | 内容审核 | 发布任务 | 监测报告        │
└─────────────────────────────────────────────────────────────┘
                              │ REST / SSE
┌─────────────────────────────────────────────────────────────┐
│  网关层 API Gateway                                          │
│  鉴权 JWT │ 租户路由 │ 限流 │ 日志                            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  业务服务层 Business Services (FastAPI)                      │
│  tenant-svc │ kb-svc │ content-svc │ publish-svc │ monitor-svc │
│  billing-svc │ report-svc                                    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  智能服务层 AI Services                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Orchestrator    │  │ Review Agents   │  │ Skill       │ │
│  │ Agent           │→ │ 合规 / 事实      │  │ Runtime     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│  Industry Pack Loader (beauty_local)                         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  数据与基础设施 Data & Infra                                  │
│  PostgreSQL │ Redis │ MinIO/OSS │ Faiss(V1.1) │ 任务队列       │
│  LLM API (DeepSeek/通义/等) │ 第三方 GEO API (可选)            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 MVP 部署形态

**建议单体 + 模块化目录**（不过早微服务）：

```
geo-platform/
├── apps/web/          # Vue 3 前端
├── apps/api/          # FastAPI 主服务
├── packages/agents/   # Orchestrator, Review
├── packages/skills/   # 平台 Skill + beauty_local Skill
├── packages/industry/ # beauty_local 行业包配置
└── infra/             # Docker Compose
```

---

## 2. 核心技术选型

| 模块 | 技术选型 | 决策理由 |
|------|---------|---------|
| 前端 | Vue 3 (Composition API) | 与团队参考项目一致，适合复杂表单与看板 |
| UI | Element Plus | 企业后台快速搭建 |
| 状态 | Pinia | 租户上下文、策略草稿、任务状态 |
| 后端 | FastAPI | 异步、类型提示、AI 生态友好 |
| 数据库 | PostgreSQL |  relational + JSON 字段存 Strategy |
| 缓存/队列 | Redis | 缓存行业包、异步 Skill/监测任务 |
| 对象存储 | MinIO / 云 OSS | 上传资料、导出包；**MVP 可用本地目录** |
| Agent 编排 | **MVP**：FastAPI + 轻量 Orchestrator（`jobs` 表状态机）<br>**V1.1**：LangGraph<br>**内部试 Prompt**：Dify/Coze（不接入生产多租户） | Orchestrator 工作流 |
| LLM | 多模型可配置 | 国内 API 为主 |
| 向量库 | **Faiss** | 痛点聚类、variants 同义扩展、RawInputs 语义检索（V1.1） |

---

## 3. 模块详细设计

### 3.1 前端架构

**核心页面：**

| 页面 | 功能 |
|------|------|
| 企业工作台 | 概览、快捷入口 |
| 知识库 | 品牌/门店/项目/**目标 AI 选择**/种子关键词/RawInput |
| 策略中心 | 策略报告、风险标注、确认/修改 |
| 内容中心 | 生成内容列表、审核、预览 |
| 发布中心 | 任务看板（draft/ready/published） |
| 监测中心 | Prompt 库、趋势图、引用来源 |
| 设置 | 成员、计费、第三方监测配置 |

**Pinia Store 划分：**

- `useAuthStore`：用户、token
- `useTenantStore`：当前企业、切换企业
- `useKbStore`：知识库编辑态
- `useStrategyStore`：策略草案、确认状态
- `useTaskStore`：发布任务、异步 Job 进度

**关键组件：**

- `StrategyReport.vue`：策略报告卡片 + 编辑
- `ContentPreview.vue`：多渠道内容预览
- `PublishExport.vue`：SEMI 一键复制
- `MonitorTrend.vue`：提及率折线
- `AgentProgress.vue`：SSE 展示 Agent/Skill 执行进度（可选）

### 3.2 Skill 运行时（AI 工具层）

参考 MCP 思想，将业务能力封装为 **Skill**，供 Orchestrator 调用。

**Skill 定义结构：**

```yaml
skill:
  name: beauty_xhs_note
  version: "1.0"
  industry: beauty_local          # 可选，空=平台通用
  prompt_template: layer1 + layer2
  tools: [kb_fetch, fact_verify]
  input_schema: { topic, fact_refs, tone }
  output_schema: { title, body, tags, cover_hint }
  constraints: [no_hallucination, compliance_beauty_general]
```

**三层 Prompt 注入：**

```
Layer 1 平台 Skill 模板（固定）
  + Layer 2 行业包 beauty_local（固定）
  + Layer 3 企业 KB 上下文（动态）
  = 最终 Prompt
```

**Skill 运行时流程：**

```
invoke_skill(name, params)
  → 加载 Skill 定义 + IndustryPack
  → tools.kb_fetch(tenant_id) 拉事实
  → 组装 Prompt → LLM
  → output_schema 校验
  → fact_verify / compliance_check
  → 返回 SkillResult
```

### 3.3 Orchestrator Agent 工作流

**MVP 实现：** 顺序调用 Skill + `jobs` 表记录状态（不过早引入 LangGraph）。

```
[KB Ready: 含 TargetEngines + SeedKeywords]
      ↓
[Load Industry Pack: beauty_local]  ← IndustryPackLoader 读预置配置
      ↓
[source_diagnose] → 按客户选引擎探测信源
      ↓
[beauty_pain_mine + keyword_mine] → KeywordLibrary 草案
      ↓
[用户确认词库]
      ↓
[Analyze KB + beauty_gap_diagnose] → content_gaps
      ↓
[Plan: engine_plan + content_units[] + monitor_plan]
      ↓
[dss_score 目标] + [Compliance/Fact Review]
      ↓
[Strategy Report] → 用户 confirm
      ↓
[Parallel Skill Execution per content_unit.outputs] → ContentAssets
      ↓
[Publish] → [monitor_run: 24h + weekly]
```

### 3.4 content_unit 与内容 Skill 协作

```yaml
# Orchestrator 为每个场景问题生成 content_unit
content_unit:
  id: cu_001
  scenario: "敏感肌能不能做皮肤管理"
  core_intent: pain
  variants:
    - "角质层薄适合做什么项目"
    - "脸一热就红还能做清洁吗"
  fact_refs: [service_03, raw_08]
  engine_targets: [doubao, deepseek]
  monitor_phrase: "敏感肌 皮肤管理 推荐"
  outputs:
    - skill: content_faq
      channel: hosted_page
      keyword_slots: [title, faq_q, summary]
    - skill: beauty_xhs_note
      channel: xiaohongshu
    - skill: beauty_zhihu_answer
      channel: zhihu
```

**禁止：** 正文重复堆砌同一关键词；无 fact_refs 的内容 fact_verify 拒发。

### 3.5 发布适配器（Publish Adapters）

```
PublishAdapter (interface)
  ├── HostedPageAdapter    # 平台托管页 AUTO
  ├── WordPressAdapter     # WP REST API（可选）
  ├── ExportAdapter        # SEMI 导出
  └── GuidedAdapter        # GUIDED 文案+指引
```

### 3.6 监测引擎

```
MonitorScheduler
  → prompts from KeywordLibrary (intent/local), grouped by TargetEngine
  → post_publish_probe: 24h after publish (quick win detection)
  → weekly_trend: 长期趋势
  → metrics: ai_answer_visibility, citation_count, source_list_exposure
```

**第三方适配器：** `OtterlyAdapter` 实现同一 `MonitorEngine` 接口，per-tenant 配置。

---

## 4. 行业包架构（beauty_local）

**职责边界：**

| 角色 | 做什么 |
|------|--------|
| 产品/工程 | 设计并维护 `industry/beauty_local/` 目录（Prompt、禁词、Skill 清单） |
| IndustryPackLoader | 租户绑定行业包时加载配置到内存/Redis |
| Orchestrator Agent | **使用**行业包规则出策略；不现场生成行业包 |

```
industry/beauty_local/
├── schema.json           # KB 字段扩展
├── prompts/              # Layer 2 Prompt
│   ├── orchestrator.yaml
│   ├── xhs_note.yaml
│   └── zhihu_answer.yaml
├── skills.manifest.json  # 启用的 Skill 列表
├── channels.json         # 信源优先级、发布模式
├── compliance/
│   └── general_beauty.txt  # 生美禁词
├── monitor/
│   └── prompt_templates.json
├── engines.json          # 引擎元数据、默认探测 Prompt 模板
└── export/
    ├── xhs_format.json
    └── dianping_guide.md
```

---

## 5. 数据库设计（核心表）

### 5.1 tenants

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| name | varchar | 企业名 |
| industry_pack | varchar | beauty_local |
| created_at | timestamp | |

### 5.2 knowledge 相关

| 表 | 关键字段 |
|----|---------|
| brands | tenant_id, name, description, positioning |
| stores | tenant_id, brand_id, name, address, phone, lat, lng, hours |
| services | tenant_id, name, description, price_min, price_max, notes |
| raw_inputs | tenant_id, type(chat/faq/script), content, source_label |
| target_engines | tenant_id, engine, priority (primary/secondary) |
| keywords | tenant_id, type, phrase, source, frequency, status |
| source_diagnoses | tenant_id, engine, payload JSONB, created_at |

### 5.3 strategies

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| tenant_id | UUID | |
| payload | JSONB | 完整 Strategy |
| status | enum | draft / confirmed / executed |
| confirmed_by | UUID | 确认人 |
| confirmed_at | timestamp | |

### 5.4 content_assets / publish_tasks / monitor_runs

见概要设计 §4.2，详细 DDL 在详细设计阶段补充。

### 5.5 Faiss 向量索引（V1.1）

```
embedding_service(text) → vector
  → Faiss Index（按 tenant_id 分索引或 metadata 过滤）
  → 用途：RawInputs 聚类、variants 同义扩展、痛点去重
PostgreSQL 存 chunk_id、tenant_id、source_ref、text；Faiss 存向量
```

---

## 6. 接口示例

### 6.1 触发分析

```http
POST /api/tenants/{tenant_id}/analyze
Authorization: Bearer {token}

Response 202:
{
  "job_id": "uuid",
  "message": "分析任务已提交"
}
```

### 6.2 确认策略并执行

```http
POST /api/strategies/{id}/confirm
Body: { "overrides": { "channels": ["hosted", "xhs"] } }

Response 200:
{
  "strategy_id": "uuid",
  "status": "confirmed",
  "execution_job_id": "uuid"
}
```

### 6.3 Skill 内部（服务内调用）

```python
result = skill_runtime.invoke(
    skill="beauty_xhs_note",
    tenant_id=tenant_id,
    params={"topic": "敏感肌清洁", "fact_refs": ["fact_12", "fact_45"]},
    strategy_id=strategy_id,
)
```

---

## 7. 部署与运维

| 项 | 方案 |
|----|------|
| 容器化 | Docker：api、web、postgres、redis |
| 编排 | Docker Compose（MVP） |
| 监控 | 结构化日志；LLM token 统计 |
| 密钥 | LLM API Key、SEO API Key 环境变量注入 |

---

## 8. 安全设计

| 项 | 措施 |
|----|------|
| 认证 | JWT，过期刷新 |
| 授权 | RBAC + tenant_id 全链路 |
| Skill | 禁止跨 tenant 读 KB |
| 爬虫 | URL 白名单、限速、User-Agent 标识 |
| 数据 | 敏感字段加密 at rest（可选 V1.1） |

---

## 9. 演进路线

| 阶段 | 架构变化 |
|------|---------|
| MVP | 单体 FastAPI + 轻量 Orchestrator + 模块化 Skill |
| V1.1 | LangGraph 编排；Faiss 向量；监测/Skill Worker 独立进程；WordPress 适配器 |
| V2 | b2b 行业包；CRM Webhook；`entity_relations` 显式关系（非 Neo4j 重型 KG） |
| V3 | 多 region；K8s；媒体 API 合作 |

---

**批准人签字：** __________  
**日期：** __________

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-07-01 | 初版 |
| V1.1 | 2026-07-02 | TargetEngines、信源诊断、KeywordLibrary、分引擎监测 |
| V1.2 | 2026-07-02 | Fact 分层、content_unit、Faiss、Orchestrator 分阶段、行业包职责 |
