# GEO 项目目录结构 v4.2

> 参考 TalentFlow AI Backend 分层；API 按 **用户端 `/user`** + **管理端 `/admin`** 拆分。

## 仓库总览

```
GEO/
├── backend/                 # FastAPI 后端
├── frontend/                # Vue3 企业用户端（管理端前端 V2+）
├── infra/                   # Docker Compose
├── docs/v4/                 # 产品 / 架构文档
└── mcp_server/              # 位于 backend/mcp_server/
```

## 后端 `backend/app/`

```
app/
├── main.py
├── api/
│   ├── common.py            # require_role 装饰器（类比 TalentFlow deps 工具）
│   ├── deps/auth.py         # re-export security 鉴权依赖
│   ├── health.py
│   └── v1/
│       ├── auth.py          # 共用 · /api/v1/auth/*
│       ├── llm.py           # 共用 · /api/v1/llm/*（类比 skills）
│       ├── agent.py         # 共用 · /api/v1/agent/*（类比 tasks）
│       ├── user/            # 用户端 · 按业务域
│       │   ├── enterprise.py    # 舱1 → /api/v1/user/enterprise
│       │   ├── kb.py
│       │   ├── onboarding.py
│       │   ├── diagnosis.py
│       │   ├── strategy_pack.py # 舱2
│       │   ├── content.py
│       │   ├── publish.py       # 舱3
│       │   ├── monitoring.py
│       │   └── outcomes.py
│       └── admin/           # 管理端 · 按业务域
│           ├── enterprises.py   # → /api/v1/admin/enterprises
│           ├── users.py
│           ├── stats.py
│           ├── agent_traces.py
│           └── llm.py           # 平台级 LLM 用量
├── core/                    # config · db · security · celery · llm/
├── models/                  # ORM，与 schemas/ 按域对齐
│   ├── auth.py              # Enterprise · User · Brand · Store · Service
│   ├── kb.py
│   ├── strategy.py
│   ├── content.py
│   ├── publish.py
│   ├── monitor.py
│   ├── audit.py
│   ├── events.py
│   └── ops.py
├── schemas/                 # Pydantic DTO
│   ├── auth.py
│   ├── kb.py
│   ├── diagnosis.py
│   ├── strategy.py
│   ├── content.py
│   ├── publish.py
│   ├── monitor.py
│   ├── agent.py
│   ├── dashboard.py
│   └── business.py          # 向后兼容 re-export
├── service/                 # 业务逻辑
├── agents/                  # LangGraph · 行业包
├── tasks/                   # Celery
└── utils/
```

## MCP Server `backend/mcp_server/`

```
mcp_server/
├── server.py          # FastMCP 独立进程
├── http_router.py     # GET /mcp/kb/*（MCP_ENABLED 时挂载到 FastAPI）
├── tools.py           # kb_fetch · kb_freshness · kb_summary（只读）
└── auth.py            # X-MCP-API-Key
```

## API 路由一览

| 前缀 | 角色 | 说明 |
|------|------|------|
| `/api/v1/auth` | 公共 | 登录 / 注册 / me |
| `/api/v1/llm` | 企业用户 | LLM Gateway（引擎 / chat / embed） |
| `/api/v1/agent` | 企业用户 | Agent 异步任务 |
| `/api/v1/user/*` | 企业用户 | 三舱 B2B 管理台（按业务域） |
| `/api/v1/admin/*` | 平台管理员 | `platform_admin` 或 `PLATFORM_ADMIN_EMAILS` |
| `/mcp/*` | MCP Key | 只读 KB 工具（可选） |

> 每个 router 文件自带完整 prefix，在 `v1/__init__.py` 扁平注册（对齐 TalentFlow `main.py`）。

## models ↔ schemas 对照

| models/ | schemas/ |
|---------|----------|
| auth.py | auth.py |
| kb.py | kb.py |
| strategy.py | strategy.py + diagnosis.py + agent.py |
| content.py | content.py |
| publish.py | publish.py |
| monitor.py | monitor.py + dashboard.py |

## 前端 `frontend/src/api/`

| 文件 | 后端前缀 |
|------|----------|
| auth.ts | `/api/v1/auth` |
| llm.ts | `/api/v1/llm` |
| enterprise.ts · kb.ts · onboarding.ts · strategy.ts | `/api/v1/user/...` |
| ops.ts | `/api/v1/user/...` + `/api/v1/agent`（草稿 / 发布 / 监测 / Agent） |
