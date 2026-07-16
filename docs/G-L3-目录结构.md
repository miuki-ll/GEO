# GEO 目录结构

> **版本**：v2.1 | **日期**：2026-07-16
> **关联**：[G-L2-架构设计说明书.md](G-L2-架构设计说明书.md) · [G-L1-PRD-v2.md](G-L1-PRD-v2.md)

---

## 项目根目录

```
GEO/
├── docs/                             # L1-L4 规范文档
│   ├── G-L1-PRD-v2.md                     # L1 产品需求文档 v2.1
│   ├── G-L1-需求规格说明书.md          # L1 功能规格 · FR/AC
│   ├── G-L1-产品介绍-生美老板版.md     # L1 客户可读
│   ├── G-L2-架构设计说明书.md               # L2 架构设计说明书
│   ├── G-L2-概要设计说明书.md          # L2 模块数据流 · 8步管道
│   ├── G-L2-数据库说明.md              # L2 22张表 · ER
│   ├── G-L3-API契约.md                # L3 API 契约
│   ├── G-L3-目录结构.md               # L3 本文件
│   ├── G-L3-实施清单.md               # L3 排期 · 验收
│   ├── G-L2-设计规范.md                     # L2 UX 视觉规范
│   ├── G-L4-验收回滚.md                   # L4 验收 & 回滚
│   ├── G-L4-测试计划.md               # L4 测试
│   ├── G-L4-部署运维手册.md           # L4 部署
│   ├── G-L4-安全规范.md               # L4 安全
│   ├── G-L4-运营手册.md               # L4 运营
│   └── rollback-history/             # 迭代归档
│
├── frontend/                         # Vue3 + Vite + TS + Element Plus
│   ├── package.json
│   ├── vite.config.ts                # 构建 · 代理
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.ts                   # 入口：app + router + pinia
│       ├── App.vue                   # fade 过渡
│       │
│       ├── views/                    # 页面（10 个模块）
│       │   ├── Login.vue
│       │   ├── Register.vue
│       │   ├── NotFound.vue
│       │   ├── onboarding/           # 舱1 开店向导
│       │   │   └── Index.vue
│       │   ├── strategy/             # 舱2 方案包 + 词库
│       │   │   └── Index.vue
│       │   ├── content/              # 舱2 草稿审核
│       │   │   └── Drafts.vue
│       │   ├── publish/              # 舱3 发布
│       │   │   └── Tasks.vue
│       │   ├── monitor/              # 舱3 监测
│       │   │   └── Index.vue
│       │   ├── outcomes/             # 舱3 效果舱
│       │   │   └── Index.vue
│       │   ├── knowledge-base/       # 知识库
│       │   │   └── Index.vue
│       │   └── settings/             # 设置 · 主攻AI修改
│       │       └── Index.vue
│       │
│       ├── api/                      # Axios 封装（8 模块）
│       │   ├── index.ts              # 实例 + 拦截器
│       │   ├── auth.ts               # login / register / fetchUser
│       │   ├── enterprise.ts         # 企业 CRUD + target_engines
│       │   ├── kb.ts                 # Fact / FAQ / Signal
│       │   ├── onboarding.ts         # POST run / GET status(SSE)
│       │   ├── strategy.ts           # strategy-pack / content-drafts
│       │   ├── llm.ts                # LLM 调试
│       │   └── ops.ts                # 运维
│       │
│       ├── stores/                   # Pinia（4 个 store）
│       │   ├── index.ts              # createPinia
│       │   ├── app.ts                # 全局状态
│       │   ├── user.ts               # JWT + 用户信息
│       │   └── onboarding.ts         # 开店向导状态
│       │
│       ├── router/
│       │   └── index.ts              # 路由表 + 守卫
│       │
│       ├── layouts/
│       │   └── DefaultLayout.vue     # 侧边栏 + 内容
│       │
│       ├── components/               # 通用组件
│       │   └── ProgressChain.vue     # Job 进度条
│       │
│       ├── types/                    # TS 类型
│       ├── utils/                    # 工具函数
│       └── assets/                   # 静态资源
│
├── backend/
│   ├── requirements.txt              # Python 依赖
│   ├── pyproject.toml
│   ├── .env / .env.example           # 环境变量
│   ├── Dockerfile
│   ├── alembic/                      # 数据库迁移
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   │       └── ac5a7237aec7_initial_schema_v2.py
│   │
│   └── app/
│       ├── main.py                   # FastAPI 入口 · CORS · lifespan
│       │
│       ├── api/v1/user/              # REST API（10 模块）
│       │   ├── __init__.py
│       │   ├── auth.py               # /register · /login · /me
│       │   ├── enterprise.py         # GET/PUT enterprise
│       │   ├── kb.py                 # CRUD Fact/FAQ/Signal
│       │   ├── onboarding.py         # POST /run · GET /status(SSE)
│       │   ├── diagnosis.py          # GET diagnosis
│       │   ├── strategy_pack.py      # GET draft · POST confirm
│       │   ├── content.py            # GET drafts · bulk-approve
│       │   ├── publish.py            # GET/POST publish tasks
│       │   ├── monitoring.py         # GET monitor results
│       │   └── outcomes.py           # GET dashboard
│       │
│       ├── models/                   # ORM（22 张表）
│       │   ├── __init__.py
│       │   ├── base.py               # TimestampMixin · TenantMixin
│       │   ├── auth.py               # Enterprise · User · RolePermission · Brand · Store · Service
│       │   ├── kb.py                 # KBFact · KBFaq · KBSignal · KBExternal
│       │   ├── strategy.py           # TargetEngine · SourceDiagnosis · Keyword · Scenario · StrategyPack* · AgentTask
│       │   ├── content.py            # ContentAsset · ContentDraft
│       │   ├── publish.py            # PublishTask
│       │   ├── monitor.py            # MonitorProfile · MonitorResult · OutcomeSnapshot
│       │   ├── audit.py              # ApprovalLog · AgentTrace
│       │   ├── events.py             # HostedPageEvent
│       │   └── ops.py                # FaissIndex
│       │
│       ├── schemas/                  # Pydantic v2 校验
│       │   ├── __init__.py
│       │   ├── _helpers.py
│       │   ├── auth.py / kb.py / business.py / common.py
│       │   ├── strategy.py / diagnosis.py / agent.py
│       │   ├── content.py / publish.py / monitor.py
│       │   └── dashboard.py
│       │
│       ├── service/                  # 业务逻辑（12 模块）
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── kb_service.py
│       │   ├── kb_freshness_service.py
│       │   ├── diagnosis_service.py
│       │   ├── scenario_service.py
│       │   ├── strategy_service.py
│       │   ├── content_service.py
│       │   ├── publish_service.py
│       │   ├── monitor_service.py
│       │   ├── dashboard_service.py
│       │   ├── agent_task_service.py
│       │   └── agent_trace_service.py
│       │
│       ├── agents/                   # Agent 运行时
│       │   ├── __init__.py
│       │   ├── harness.py            # ReAct Harness + ToolRegistry
│       │   ├── runner.py             # LangGraph Runner
│       │   ├── registry.py           # Graph 注册表
│       │   ├── state.py              # AgentGraphState
│       │   ├── graphs/
│       │   │   └── onboarding/
│       │   │       ├── __init__.py
│       │   │       ├── graph.py      # 注册 "onboarding"
│       │   │       ├── nodes.py      # DIAGNOSE → PAIN → PERSONA → COMPETITOR
│       │   │       ├── state.py
│       │   │       └── edges.py
│       │   └── industry/             # 行业包
│       │       ├── __init__.py
│       │       ├── base.py           # IndustryPack 抽象基类
│       │       ├── registry.py       # 注册表
│       │       └── packs/
│       │           └── beauty_local/
│       │               ├── __init__.py
│       │               ├── pack.py   # BeautyLocalPack
│       │               ├── templates.py  # 规则簿 · few-shot
│       │               └── seed.py   # 种子数据（测试用）
│       │
│       ├── core/                     # 基础设施
│       │   ├── __init__.py
│       │   ├── config.py             # Pydantic Settings
│       │   ├── db.py                 # SQLAlchemy session
│       │   ├── security.py           # JWT + 密码哈希
│       │   ├── celery_app.py         # Celery 配置
│       │   ├── celery.py             # Celery 实例
│       │   ├── embedding.py          # Faiss embedding
│       │   ├── logging_config.py     # 日志
│       │   └── llm/                  # LLM Gateway
│       │       ├── __init__.py
│       │       ├── gateway.py        # chat() / simple_prompt()
│       │       ├── schemas.py        # LLMRequest / LLMResponse
│       │       ├── base.py           # BaseEngineAdapter
│       │       └── adapters.py       # OpenAI-compat × 4
│       │
│       ├── tools/                    # Agent 工具
│       ├── crud/                     # 通用 CRUD
│       ├── rag/                      # RAG 检索
│       ├── tasks/                    # Celery 任务
│       └── utils/                    # 工具
│
├── playbooks/                        # 品类 SOP 剧本
├── 策略/                             # 方法论分析
│   └── A/S/A/
│       ├── 完整策略.md
│       ├── T-GEO五层架构详解.md
│       ├── 实施方案vsPRD差异分析.md
│       └── API探针.md
├── 资料/                             # 参考基线
├── GEO平台实施方案.md                # 业务方案
├── PRD沟通文档.md                    # 决策记录
├── .gitignore
└── README.md
```

---

## 文件命名约定

| 约定 | 说明 |
|------|------|
| Vue 页面 | 首字母大写 · 语义化路由名：`Login.vue` `Drafts.vue` |
| Vue 目录 | kebab-case：`knowledge-base/` `strategy-pack/` |
| Python 模块 | snake_case：`diagnosis_service.py` `strategy_pack.py` |
| Python 类 | PascalCase：`BeautyLocalPack` `AgentGraphState` |
| ORM 表 | snake_case 复数：`enterprises` `kb_facts` `publish_tasks` |
| API 路径 | kebab-case：`/strategy-pack/draft` `/content-drafts` |
| 文档 | 中文名 + 语义：`G-L1-需求规格说明书.md` |

---

## 禁止行为

| 禁止 | 替代 |
|------|------|
| 在 `views/` 外新建页面目录 | 统一放 `views/` 下 |
| API 调用裸 `fetch` | 走 `api/` Axios 实例 |
| 后端裸 `dict` 传参 | 走 `schemas/` Pydantic 校验 |
| Agent 工具写 `write_fact`/`publish` | ToolRegistry 白名单禁止 |
| 新建 ORM 表不写 Alembic 迁移 | `alembic revision --autogenerate` |

---

*目录结构 v2.1 · 完全对齐代码基线*
