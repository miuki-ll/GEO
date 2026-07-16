# ARCHITECTURE — 架构设计说明书 v2.0

> **版本**：v2.0 · 对齐 PRD v2.1 + 代码基线 | **日期**：2026-07-16
> **关联**：[G-L1-PRD-v2.md](G-L1-PRD-v2.md) · [G-L2-设计规范.md](G-L2-设计规范.md) · [G-L4-验收回滚.md](G-L4-验收回滚.md)

---

## 1. 技术栈

### 1.1 前端

| 项 | 选型 | 版本 |
|----|------|------|
| 框架 | Vue 3（Composition API + `<script setup>`） | ^3.4 |
| 构建 | Vite | ^5.4 |
| 语言 | TypeScript | ^5.5 |
| UI 库 | Element Plus + `@element-plus/icons-vue` | ^2.8 |
| 状态管理 | Pinia + `pinia-plugin-persistedstate` | ^2.2 |
| 路由 | Vue Router | ^4.4 |
| HTTP | Axios（拦截器统一鉴权 + 错误处理） | ^1.7 |
| 图表 | ECharts + `vue-echarts` | ^5.5 |
| 日期 | dayjs | ^1.11 |
| 进度条 | nprogress | ^0.2 |

### 1.2 后端

| 项 | 选型 | 版本 |
|----|------|------|
| 语言 | Python | 3.11+ |
| Web 框架 | FastAPI + uvicorn | >=0.115 |
| 数据校验 | Pydantic v2 + pydantic-settings | >=2.9 |
| ORM | SQLAlchemy 2.0 + PyMySQL | >=2.0 |
| 迁移 | Alembic | >=1.13 |
| 任务队列 | Celery + Redis | >=5.4 |
| JWT | python-jose + passlib[bcrypt] + argon2-cffi | >=3.3 |
| HTTP/重试 | httpx + tenacity | >=0.27 |
| 限流 | slowapi + limits | >=0.1 |
| 向量检索 | Faiss (CPU) + numpy + pandas | >=1.9 |
| 可观测 | Sentry SDK + LangSmith | >=2.16 |
| MCP | fastmcp | >=2.0 |
| 测试 | pytest + pytest-asyncio | >=8.3 |
| LLM 编排 | LangGraph + langchain-core | >=0.2 |

### 1.3 基础设施

| 项 | 环境 | 说明 |
|----|------|------|
| 部署 | Docker Compose（3 容器） | api:8000 + web:5173 + pg:5432 |
| 数据库 | PostgreSQL | 自建或 RDS |
| 缓存/队列 | Redis | Celery broker + result backend |
| 对象存储 | OSS / S3 兼容 | 托管页静态文件 |
| 监控 | Sentry + LangSmith | 错误 + LLM trace |

---

## 2. 架构分层

```
┌──────────────────────────────────────────────────────────────┐
│                      前端 (Vue3 + Vite)                        │
│  views/          stores/         api/          components/    │
│  onboarding/     onboarding.ts   auth.ts       ProgressChain  │
│  strategy/       app.ts          enterprise.ts                │
│  content/        user.ts         kb.ts                        │
│  publish/                        onboarding.ts                │
│  monitor/                        strategy.ts                  │
│  outcomes/                       llm.ts                       │
│  knowledge-base/                 ops.ts                       │
│  settings/                                                   │
└───────────────────────────┬──────────────────────────────────┘
                            │ Axios + JWT Bearer Token
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    API 网关 (FastAPI)                          │
│  /api/v1/user/                                                │
│  onboarding.py   diagnosis.py    strategy_pack.py             │
│  content.py      publish.py      monitoring.py                │
│  outcomes.py     kb.py           enterprise.py                │
│                                                               │
│  schemas/  ← Pydantic v2 校验 · extra=forbid                  │
│  service/  ← 业务逻辑 · 租户隔离强制 filter(enterprise_id=)     │
└───────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
│  Agent Runtime   │ │  Celery  │ │   LLM Gateway    │
│  ─────────────   │ │  Worker  │ │   ────────────   │
│  harness.py      │ │  + Beat  │ │   gateway.py     │
│  registry.py     │ │          │ │   schemas.py     │
│  runner.py       │ │  定时监测 │ │   adapters.py    │
│  state.py        │ │  异步Job │ │   4 EngineAdapter │
│                  │ │          │ │                   │
│  graphs/         │ │          │ │   豆包 DeepSeek   │
│  └─ onboarding/  │ │          │ │   Kimi 文心一言   │
│      graph.py    │ │          │ │                   │
│      nodes.py    │ │          │ │                   │
│      state.py    │ │          │ │                   │
│                  │ │          │ │                   │
│  industry/       │ │          │ │                   │
│  ├─ base.py      │ │          │ │                   │
│  ├─ registry.py  │ │          │ │                   │
│  └─ packs/       │ │          │ │                   │
│      └─ beauty_local/        │ │                   │
│           pack.py            │ │                   │
│           templates.py       │ │                   │
└─────────────────┘ └──────────┘ └──────────────────┘
         │                                 │
         └─────────────┬───────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    数据层 (PostgreSQL)                         │
│  auth / kb / strategy / content / publish / monitor           │
│  audit / events / ops                                         │
│  ← 22 张表 · 全 enterprise_id 隔离                            │
│  ← Alembic 迁移 · Faiss 向量 per-tenant                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 目录结构

```
GEO/
├── docs/                             # 规范文档（L1-L4）
│   ├── G-L1-PRD-v2.md                     # L1 产品需求 · v2.1
│   ├── G-L2-架构设计说明书.md               # L2 本文件
│   ├── G-L2-设计规范.md                     # L2 UI 规范
│   ├── G-L4-验收回滚.md                   # L4 验收 & 回滚
│   └── rollback-history/             # 迭代归档
│
├── frontend/                         # Vue3 前端
│   ├── vite.config.ts                # 构建配置 + API 代理
│   ├── tsconfig.json                 # TS 严格模式
│   ├── package.json                  # 依赖
│   └── src/
│       ├── main.ts                   # 入口：createApp + router + pinia
│       ├── App.vue                   # 根组件（fade 过渡）
│       │
│       ├── views/                    # 页面（按舱分组）
│       │   ├── Login.vue             # 登录
│       │   ├── Register.vue          # 注册
│       │   ├── NotFound.vue          # 404
│       │   ├── onboarding/           # 舱1 开店向导
│       │   ├── strategy/             # 舱2 方案包
│       │   ├── content/              # 舱2 草稿审核
│       │   ├── publish/              # 舱3 发布
│       │   ├── monitor/              # 舱3 监测
│       │   ├── outcomes/             # 舱3 效果舱
│       │   ├── knowledge-base/       # 知识库管理
│       │   └── settings/             # 企业/用户/主攻AI设置
│       │
│       ├── api/                      # Axios 封装
│       │   ├── index.ts              # 实例 + 拦截器
│       │   ├── auth.ts               # login / register / fetchUser
│       │   ├── enterprise.ts         # 企业 CRUD
│       │   ├── kb.ts                 # Fact / FAQ / Signal CRUD
│       │   ├── onboarding.ts         # POST run / GET status (SSE)
│       │   ├── strategy.ts           # strategy-pack / content-drafts
│       │   ├── llm.ts                # LLM 调试接口
│       │   └── ops.ts                # 运维接口
│       │
│       ├── stores/                   # Pinia
│       │   ├── index.ts              # createPinia
│       │   ├── app.ts                # 全局状态
│       │   ├── user.ts               # 用户/Auth + JWT
│       │   └── onboarding.ts         # 开店向导状态
│       │
│       ├── router/
│       │   └── index.ts              # 路由表 + 守卫（JWT 校验）
│       │
│       ├── layouts/
│       │   └── DefaultLayout.vue     # 侧边栏 + 顶栏 + 内容区
│       │
│       ├── components/               # 通用组件
│       │   └── ProgressChain.vue     # Job 进度条
│       │
│       ├── types/                    # TS 类型定义
│       ├── utils/                    # 工具函数
│       └── assets/                   # 静态资源
│
├── backend/
│   ├── requirements.txt              # Python 依赖
│   ├── .env / .env.example           # 环境变量
│   ├── alembic/                      # 数据库迁移
│   │   ├── alembic.ini
│   │   └── versions/
│   │       └── ac5a7237aec7_initial_schema_v2.py
│   │
│   └── app/
│       ├── main.py                   # FastAPI 入口 · CORS · lifespan
│       │
│       ├── api/v1/user/              # REST API（10 模块）
│       │   ├── onboarding.py         # POST /onboarding/run · GET status
│       │   ├── diagnosis.py          # GET diagnosis/* · POST probe
│       │   ├── strategy_pack.py      # GET draft · POST confirm
│       │   ├── content.py            # GET drafts · POST bulk-approve
│       │   ├── publish.py            # GET/POST publish tasks
│       │   ├── monitoring.py         # GET/POST monitor profiles & results
│       │   ├── outcomes.py           # GET dashboard aggregate
│       │   ├── kb.py                 # CRUD Fact/FAQ/Signal
│       │   └── enterprise.py         # enterprise/user CRUD
│       │
│       ├── models/                   # ORM（22 张表）
│       │   ├── base.py               # TimestampMixin · TenantMixin
│       │   ├── auth.py               # Enterprise · User · RolePermission · Brand · Store · Service
│       │   ├── kb.py                 # KBFact · KBFaq · KBSignal · KBExternal
│       │   ├── strategy.py           # TargetEngine · SourceDiagnosis · Keyword · Scenario · StrategyPack · AgentTask
│       │   ├── content.py            # ContentAsset · ContentDraft
│       │   ├── publish.py            # PublishTask
│       │   ├── monitor.py            # MonitorProfile · MonitorResult · OutcomeSnapshot
│       │   ├── audit.py              # ApprovalLog · AgentTrace
│       │   ├── events.py             # HostedPageEvent
│       │   └── ops.py                # FaissIndex
│       │
│       ├── schemas/                  # Pydantic v2 校验（与 models 按域对应）
│       │   ├── _helpers.py           # 通用工具
│       │   ├── auth.py / kb.py / business.py
│       │   ├── strategy.py / diagnosis.py / agent.py
│       │   ├── content.py / publish.py / monitor.py
│       │   ├── dashboard.py / common.py
│       │
│       ├── service/                  # 业务逻辑（12 模块）
│       │   ├── auth_service.py       # 注册/登录/JWT
│       │   ├── kb_service.py         # Fact/FAQ/Signal CRUD
│       │   ├── kb_freshness_service.py
│       │   ├── diagnosis_service.py  # 探针/赛道/信源地图
│       │   ├── scenario_service.py   # Scenario CRUD
│       │   ├── strategy_service.py   # 方案包构建
│       │   ├── content_service.py    # 内容生成 + 审核
│       │   ├── publish_service.py    # 发布调度
│       │   ├── monitor_service.py    # Core/Probe 监测
│       │   ├── dashboard_service.py  # 效果舱聚合
│       │   ├── agent_task_service.py # Agent 任务管理
│       │   └── agent_trace_service.py # Agent 审计
│       │
│       ├── agents/                   # Agent 运行时
│       │   ├── harness.py            # ReAct Harness + ToolRegistry
│       │   ├── runner.py             # LangGraph Runner
│       │   ├── registry.py           # Graph 注册表
│       │   ├── state.py              # AgentGraphState
│       │   ├── graphs/
│       │   │   └── onboarding/       # 入驻 Job 链
│       │   │       ├── graph.py      # graph 注册 => "onboarding"
│       │   │       ├── nodes.py      # DIAGNOSE → PAIN → PERSONA → COMPETITOR
│       │   │       ├── state.py      # 节点状态
│       │   │       └── edges.py      # 条件分支
│       │   └── industry/             # 行业包系统
│       │       ├── base.py           # IndustryPack 抽象基类
│       │       ├── registry.py       # 行业包注册表
│       │       └── packs/
│       │           └── beauty_local/ # 生美行业包
│       │               ├── pack.py   # BeautyLocalPack(IndustryPack)
│       │               ├── templates.py  # 禁词/渠道权重/合规/Few-shot
│       │               └── seed.py   # 种子企业（测试用）
│       │
│       ├── core/                     # 基础设施
│       │   ├── config.py             # Pydantic Settings · 环境变量
│       │   ├── db.py                 # SQLAlchemy session
│       │   ├── security.py           # JWT encode/decode + 密码哈希
│       │   ├── celery_app.py         # Celery 配置
│       │   ├── celery.py             # Celery 实例
│       │   ├── embedding.py          # Faiss embedding
│       │   ├── logging_config.py     # 日志配置
│       │   └── llm/                  # LLM Gateway
│       │       ├── gateway.py        # chat() / simple_prompt()
│       │       ├── schemas.py        # LLMRequest / LLMResponse / LLMUsage
│       │       ├── base.py           # BaseEngineAdapter
│       │       └── adapters.py       # OpenAI-compat Adapter × 4
│       │
│       ├── tools/                    # Agent 工具
│       ├── crud/                     # 通用 CRUD 基类
│       ├── rag/                      # RAG 检索（未来）
│       ├── tasks/                    # Celery 任务定义
│       └── utils/                    # 工具函数
│
├── playbooks/                        # 品类 SOP 剧本
├── 策略/                             # 方法论分析文档
│   └── A/S/A/
│       ├── 完整策略.md
│       ├── T-GEO五层架构详解.md
│       └── 实施方案vsPRD差异分析.md
├── 资料/                             # 参考资料
└── GEO平台实施方案.md                # 业务方案 · 方法论源
```

---

## 4. 数据模型

### 4.1 ER 总览（22 张表 · 按域分 8 组）

```
┌────────────────────────────────────────────────────────────────┐
│                         核心模型 ER                              │
│                                                                 │
│  Enterprise ──────────────────────────────────────────────┐     │
│  │ id, name, industry, industry_pack,                    │     │
│  │ license_no, plan, kb_updated_at                       │     │
│  │                                                        │     │
│  ├── User (owner/admin/editor/viewer)                     │     │
│  ├── Brand (品牌信息)                                      │     │
│  ├── Store[] (多门店 · NAP)                                │     │
│  ├── Service[] (项目 · 价格区间)                           │     │
│  │                                                        │     │
│  ├── KBFact[] / KBFaq[] / KBSignal[] / KBExternal[]      │     │
│  │                                                        │     │
│  ├── TargetEngine[] ──────────────────────┐               │     │
│  │  (含租户级 target_engines 配置)         │               │     │
│  │                                        │               │     │
│  ├── SourceDiagnosis[]                    │               │     │
│  ├── Keyword[] (四层词库 · 标来源)         │               │     │
│  ├── Scenario[]                           │               │     │
│  ├── StrategyPackDraft → StrategyPack     │               │     │
│  ├── AgentTask[]                          │               │     │
│  │                                        │               │     │
│  ├── ContentAsset[] / ContentDraft[]      │               │     │
│  ├── PublishTask[] (content_asset_id)      │               │     │
│  │                                        │               │     │
│  ├── MonitorProfile[]                     │               │     │
│  │   └── MonitorResult[]                  │               │     │
│  ├── OutcomeSnapshot[]                    │               │     │
│  │                                        │               │     │
│  ├── ApprovalLog[] (人闸门)               │               │     │
│  ├── AgentTrace[] (审计)                  │               │     │
│  ├── HostedPageEvent[] (转化追踪)         │               │     │
│  └── FaissIndex[] (per-tenant 向量)       │               │     │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 表清单

| 域 | 表名 | 说明 | 关键字段 |
|----|------|------|----------|
| **Auth** | `enterprises` | 租户 | industry, industry_pack, plan, kb_updated_at |
| | `users` | 用户 | role(owner/admin/editor/viewer), enterprise_id |
| | `role_permissions` | 角色权限 | role, permission |
| | `brands` | 品牌 | name, logo_url, differentiator |
| | `stores` | 门店 | name, address, lat, lng, phone, hours |
| | `services` | 服务项目 | name, price_range, duration, target_group |
| **KB** | `kb_facts` | Fact 层 | title, content, source_type, verified, category, tags |
| | `kb_faqs` | FAQ | question, answer, source_ref |
| | `kb_signals` | Signal 层 | signal_type, content, source, confidence, expires_at |
| | `kb_externals` | External 候选 | url, raw_content, confirmed(Fact) |
| **Strategy** | `target_engines` | AI 平台定义 | code, name, base_url, adapter, enabled |
| | `source_diagnoses` | 信源诊断结果 | engine_code, prompt, brand_mentioned, rank, hallucination |
| | `keywords` | 四层词库 | keyword, layer(认知/选型/痛点/场景), source, lbs_tags |
| | `scenarios` | 场景问句 | user_query, intent, channel, skill, fact_refs[] |
| | `strategy_pack_drafts` | 方案包草案 | persona, competitors, scenarios, channels, weights |
| | `strategy_packs` | 确认方案包 | + approved_at, approved_by |
| | `agent_tasks` | Agent 任务 | task_type, graph_name, status, progress_pct |
| **Content** | `content_assets` | 发布内容 | scenario_id, channel, body, fact_refs[], status |
| | `content_drafts` | 草稿 | content_asset_id, status(draft/ready/published) |
| **Publish** | `publish_tasks` | 发布任务 | content_asset_id, channel, mode(AUTO/SEMI/GUIDED), status |
| **Monitor** | `monitor_profiles` | 监测配置 | pool_type(Core/Probe), engine_codes[], prompt_list[] |
| | `monitor_results` | 监测结果 | profile_id, engine_code, prompt, mentioned, hallucination |
| | `outcome_snapshots` | 效果快照 | date, mention_rate, trust_score, lead_count, conversion_count |
| **Audit** | `approval_logs` | 审批记录 | target_type(strategy/content), action(confirm/reject), user_id |
| | `agent_traces` | Agent 审计 | job_id, graph_name, step_idx, thought/action/observation, tokens |
| **Events** | `hosted_page_events` | 托管页埋点 | page_url, event_type(page_view/form_submit), referer |
| **Ops** | `faiss_indexes` | Faiss 索引 | index_name, dimension, ntotal, enterprise_id |

### 4.3 核心约束

| 约束 | 说明 |
|------|------|
| **租户隔离** | 所有业务表含 `enterprise_id`，service 层强制 `filter(enterprise_id=current)` |
| **fact_refs 可追溯** | `content_assets.fact_refs` JSON 数组，值 = `kb_facts.id`，生成时注入 |
| **content_asset_id 追踪** | `publish_tasks.content_asset_id` → `content_assets.id` → `scenarios.id` → `kb_facts.id` |
| **approval_log 不可删** | 人闸门记录永久保留，审计用 |
| **Alembic 前向兼容** | 仅新增字段/表，不删不改已有字段 |

---

## 5. Agent ToB 三层

### 5.1 层级映射

```
L1 · LLM Gateway（通用）
  4 EngineAdapter：豆包 / DeepSeek / Kimi / 文心一言
  统一接口：chat() / stream() / token_count()
  所有 LLM 调用经此层，前端不直接调

L2 · Harness（编排执行）
  LangGraph 子图：onboarding_graph（DIAGNOSE→PAIN→PERSONA→COMPETITOR）
  ReAct Harness：ToolRegistry（只读工具）+ max_steps + tenant 隔离
  Celery Job：异步执行 graph，SSE 推送进度
  Skill Runtime（正文生成）：kb_fetch → LLM → fact_verify（固定链 · 不用 ReAct）
  
L3 · 垂域 IndustryPack（行业壁垒）
  行业包 = 规则簿 + few-shot 提示（不含内容种子）
  beauty_local pack：
    - forbidden_words / banned_patterns
    - channel_defaults / competitor_types
    - compliance_checklist / persona_hint
    - probe_few_shot / scenario_few_shot
    - cta_mapping / priority_verification
```

### 5.2 Agent 安全约束

| 规则 | 说明 |
|------|------|
| **禁止 write_fact** | Agent 无权写入 KB Fact |
| **禁止 auto_confirm** | Agent 无权跳过人闸门 |
| **禁止 publish** | Agent 无权直接发布 |
| **正文 Skill 无 ReAct** | 固定链 `kb_fetch → LLM → fact_verify`，不循环 |
| **ReAct max_steps ≤ 5** | competitor_graph/gap_graph 限制步数 |
| **tenant 隔离** | ToolRegistry 注入 enterprise_id，所有查询强制过滤 |

---

## 6. 8 步管道映射

```
PRD 步骤              系统实现                    Agent 角色
────────              ────────                   ──────────
1. 入驻建库            POST /onboarding/run       无 Agent
                      → Enterprise/Brand/Store/
                        Service/KBFact 写入
                      → 托管页 + Schema + llms.txt

2. 诊断 agent          onboarding_graph           诊断 agent (L2)
                      DIAGNOSE 节点:               LLM 生成探针 → EngineAdapter 测试
                      5 项全量产出                  采集信源 URL → 信源地图
                      → SourceDiagnosis 入库

3. 意图词库            pain_mine + keyword_mine    聚类 agent (L2)
                      四源汇聚:                    Faiss + LLM 簇命名
                      RawInputs + 探针反推
                      + SEO API + LLM 生成
                      → Keyword 入库 (四层标注)

4. 策略生成            POST strategy-pack/confirm  策略 agent (L2)
                      persona_analyze (LLM)        LLM 画像 + scenario 候选
                      competitor_analyze (LLM)     LLM 竞品拆解
                      渠道权重混合计算
                      → StrategyPack 入库 · 闸门①

5. 内容工厂            SkillRuntime                内容 agent (L1 固定链)
                      kb_fetch → LLM → 输出       不用 ReAct
                      7段式模板 · RAG切片(步骤5)
                      → ContentDraft 入库

6. 内容检测            fact_verify + 禁词           检测 agent (L2 固定链)
                      + 交叉验证 + 实体校验        不用 ReAct
                      + RAG可检索性(步骤6)
                      → draft → ready · 闸门②

7. 发布 agent          POST publish                发布 agent
                      AUTO: 托管页 / 合作平台
                      SEMI: 小红书/知乎 导出包
                      GUIDED: 点评/美团 指引
                      → PublishTask 入库

8. 监控迭代            Celery Beat 定时任务         监控 agent (L2)
                      Core ~20/engine              EngineAdapter
                      Probe ≤10/engine             T0/T1 对比
                      临界检测 → gap_analyze
                      → OutcomeSnapshot
```

---

## 7. 行业包系统

### 7.1 IndustryPack 抽象基类

```python
# agents/industry/base.py

class IndustryPack:
    code: str          # "beauty_local"
    name: str          # "生美本地 · 皮肤管理"

    # === 硬配：规则（人手维护）===
    def forbidden_words(self) -> List[str]: ...
    def banned_patterns(self) -> List[str]: ...
    def compliance_checklist(self) -> List[Dict]: ...
    def channel_defaults(self) -> List[Dict]: ...
    def competitor_types(self) -> List[Dict]: ...
    def cta_mapping(self) -> Dict: ...
    def priority_verification(self) -> str: ...

    # === 软配：few-shot（给 LLM 的提示 · 不是种子数据）===
    def persona_hint(self) -> Dict: ...
    def probe_few_shot(self) -> List[str]: ...
    def scenario_few_shot(self) -> List[str]: ...

    # === 不提供（全部 LLM 动态生成）===
    # probe_prompts, persona_profiles, keyword_library,
    # scenarios, competitor_profiles, fact_templates
    # → 全部在流程中由 LLM 生成，租户天然隔离
```

### 7.2 注册与激活

```
入驻时：
  用户选品类 → enterprise.industry_pack = "beauty_local"
  → IndustryRegistry.get("beauty_local") → 加载 BeautyLocalPack
  → 规则簿注入租户级配置（禁词/合规/渠道）
  → 后续 8 步均通过 pack 对象获取行业参数

运行时：
  industry = get_industry_pack(enterprise.industry_pack)
  forbidden_words = industry.forbidden_words()     # 给检测 agent
  persona_hint = industry.persona_hint()           # 给 LLM 画像生成
  probe_few_shot = industry.probe_few_shot()      # 给 LLM 探针生成
  scenario_few_shot = industry.scenario_few_shot() # 给 LLM scenario 生成
```

### 7.3 新增品类步骤

```
1. 创建 agents/industry/packs/{category}/
2. 编写 pack.py（继承 IndustryPack · 配 9 项）
3. 编写 templates.py（数据常量）
4. 注册到 registry.py
5. 验证：8 步管道不改代码跑通
6. 预计耗时：1-2 周/品类（主要是规则簿调优 + LLM 输出质量验证）
```

---

## 8. API 契约

### 8.1 统一格式

```json
// 成功
{ "code": 0, "data": {...}, "msg": "ok" }

// 失败
{ "code": 400, "data": null, "msg": "参数错误" }
```

| code | 含义 |
|------|------|
| 0 | 成功 |
| 400 | 参数错误 |
| 401 | 未登录（JWT 过期/无效） |
| 403 | 无权限（跨租户访问） |
| 404 | 资源不存在 |
| 422 | Pydantic 校验失败 |
| 500 | 服务端错误 |

### 8.2 路由表

| 舱 | 方法 | 路径 | 说明 |
|----|------|------|------|
| — | POST | `/api/v1/auth/register` | 注册 |
| — | POST | `/api/v1/auth/login` | 登录 → JWT |
| — | GET | `/api/v1/auth/me` | 当前用户信息 |
| 舱1 | POST | `/api/v1/user/onboarding/run` | 提交开店向导 → 触发 onboarding_graph |
| 舱1 | GET | `/api/v1/user/onboarding/status/{task_id}` | SSE 进度 |
| 舱1 | GET | `/api/v1/user/diagnosis/{id}` | 诊断报告详情 |
| 舱1 | POST | `/api/v1/user/diagnosis/probe` | 手动触发探针 |
| 舱1 | GET | `/api/v1/user/kb/facts` | KB Fact 列表 |
| 舱1 | POST | `/api/v1/user/kb/facts` | 新增 Fact |
| 舱1 | GET | `/api/v1/user/keywords` | 四层词库 |
| 舱1 | POST | `/api/v1/user/keywords` | 新增词条 |
| 舱2 | GET | `/api/v1/user/strategy-pack/draft` | 方案包草案（五区） |
| 舱2 | POST | `/api/v1/user/strategy-pack/confirm` | 确认方案包 · 闸门① |
| 舱2 | GET | `/api/v1/user/content/drafts` | 草稿列表 |
| 舱2 | POST | `/api/v1/user/content/drafts/{id}/approve` | 单条通过 |
| 舱2 | POST | `/api/v1/user/content/drafts/bulk-approve` | 批量通过 · 闸门② |
| 舱3 | GET | `/api/v1/user/publish/tasks` | 发布任务列表 |
| 舱3 | POST | `/api/v1/user/publish/run` | 执行发布 |
| 舱3 | GET | `/api/v1/user/monitor/results` | 监测结果 · T0/T1 对比 |
| 舱3 | GET | `/api/v1/user/outcomes/dashboard` | 效果舱汇总 |
| — | GET | `/api/v1/user/enterprise` | 企业详情 |
| — | PUT | `/api/v1/user/enterprise` | 更新企业（含 target_engines） |

### 8.3 分页规范

```
GET /api/v1/user/xxx?page=1&page_size=20
→ { items: [...], total: N, page: 1, page_size: 20 }
```

---

## 9. 前端架构

### 9.1 路由表

| 路由 | 页面 | 舱 | 说明 |
|------|------|:--:|------|
| `/login` | Login.vue | — | 登录（public） |
| `/register` | Register.vue | — | 注册（public） |
| `/onboarding` | onboarding/Index.vue | 舱1 | 开店向导 |
| `/strategy-pack` | strategy/Index.vue | 舱2 | 方案包 + 词库确认 |
| `/content/drafts` | content/Drafts.vue | 舱2 | 草稿审核 · 人闸门 |
| `/outcomes` | outcomes/Index.vue | 舱3 | 效果舱（默认首页） |
| `/publish/tasks` | publish/Tasks.vue | 舱3 | 发布任务 |
| `/monitor` | monitor/Index.vue | 舱3 | 监测看板 |
| `/knowledge-base` | knowledge-base/Index.vue | — | 知识库管理 |
| `/settings` | settings/Index.vue | — | 企业设置 · 主攻AI修改 |
| `/:pathMatch(.*)*` | NotFound.vue | — | 404 |

### 9.2 状态管理

| Store | 用途 |
|-------|------|
| `app.ts` | 全局状态（侧边栏折叠/主题） |
| `user.ts` | 用户信息/JWT/登录态 · persisted |
| `onboarding.ts` | 开店向导多步表单状态 |

### 9.3 构建产物

```
前端构建 (vite build)：
  vue-vendor.[hash].js   → Vue/VueRouter/Pinia
  element-plus.[hash].js  → Element Plus
  echarts.[hash].js       → ECharts
  业务代码.[hash].js      → 页面 + 组件
```

---

## 10. 部署架构

### 10.1 MVP 部署（Docker Compose）

```yaml
# docker-compose.yml
services:
  api:
    build: backend/
    ports: ["8000:8000"]
    depends_on: [pg, redis]
    env_file: backend/.env
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/faiss_data:/app/faiss_data

  web:
    build: frontend/
    ports: ["5173:80"]
    depends_on: [api]

  pg:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: geo
      POSTGRES_USER: geo
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine

  celery_worker:
    build: backend/
    command: celery -A app.core.celery_app worker -l info
    depends_on: [pg, redis]

  celery_beat:
    build: backend/
    command: celery -A app.core.celery_app beat -l info
    depends_on: [pg, redis]
```

### 10.2 环境变量（backend/.env）

```bash
# App
APP_ENV=development
SECRET_KEY=xxx
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql://geo:xxx@pg:5432/geo

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# LLM Engines
DOUBAO_API_KEY=xxx
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DEEPSEEK_API_KEY=xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
KIMI_API_KEY=xxx
KIMI_BASE_URL=https://api.moonshot.cn/v1
WENXIN_API_KEY=xxx
WENXIN_SECRET_KEY=xxx

# Observability
SENTRY_DSN=xxx
LANGSMITH_API_KEY=xxx
LANGSMITH_PROJECT=geo-local-mvp

# OSS
OSS_ENDPOINT=xxx
OSS_BUCKET=geo-hosted-pages
```

### 10.3 生产扩展路径

```
MVP (Docker Compose) → V1.1 (ECS + RDS + ElastiCache)

  当前                     V1.1
  ────                     ────
  docker compose up        ECS Fargate (api + web)
  pg 容器                  RDS PostgreSQL (Multi-AZ)
  redis 容器               ElastiCache Redis
  本地存储                 S3/OSS (托管页 + Faiss)
  手动备份                 RDS 自动备份 + 跨区 DR
```

---

## 11. 安全红线

| 规则 | 实现 |
|------|------|
| **租户隔离** | Service 层 `filter(enterprise_id=current_user.enterprise_id)` |
| **JWT 鉴权** | 所有 API（除 public）通过 `get_current_user` 依赖注入 |
| **跨租户 403** | API 层捕获跨 enterprise_id 访问，返回 403 |
| **密钥安全** | Engine API Key 通过平台管理员注入，前端不可见 |
| **托管页 CSP** | 发布前 HTML sanitize + Content-Security-Policy |
| **渠道凭证加密** | 小红书/知乎账号密码 AES 加密存储 |
| **Agent 只读** | ToolRegistry 禁止 write_fact / auto_confirm / publish |
| **无蒸馏 NAP** | V2+ 偏好学习禁止蒸馏价格/NAP/参数 |

---

## 12. 验收对齐（AC-01 ~ AC-15）

| AC | 架构覆盖点 |
|----|-----------|
| AC-01 | 8 步管道 → onboarding_graph + SkillRuntime + publish + monitor |
| AC-02 | fact_refs → content_assets.fact_refs JSON → kb_facts.id |
| AC-03 | 禁词 → IndustryPack.forbidden_words() → fact_verify |
| AC-04 | 探针 LLM 生成 → DIAGNOSE 节点 LLM 生成 prompt → EngineAdapter |
| AC-05 | 词库租户隔离 → Faiss per-tenant + enterprise_id 过滤 |
| AC-06 | persona LLM 生成 → PERSONA 节点 LLM 分析 RawInputs |
| AC-07 | scenario LLM 生成 → StrategyPackBuilder scenario 候选生成 |
| AC-08 | 渠道权重 → source_weight_builder 内部固定 0.6 + 探针实测 0.4 |
| AC-09 | RAG 切片 → 步骤5 SkillRuntime 自动切 + 步骤6 验证 |
| AC-10 | 5 项机审 → fact_verify + 禁词 + 交叉验证 + 实体校验 + RAG |
| AC-11 | 人闸门 → approval_logs (target_type + action) |
| AC-12 | T0/T1 对比 → monitor_results (baseline_flag=true/false) |
| AC-13 | 主攻 AI 联动 → Enterprise.target_engines → EngineAdapter 选择 |
| AC-14 | 租户隔离 → service 层 filter + API 层 403 |
| AC-15 | 行业包薄配置 → IndustryPack 基类 9 方法 + LLM 动态生成 |

---

*ARCHITECTURE v2.0 · 完全对齐代码基线 + PRD v2.1*
