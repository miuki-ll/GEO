# GEO 智能品牌平台 — 架构设计说明书 v2

> **版本**：V2.5 | **日期**：2026-07-04 | **关联**：PRD-v3.md §7 · 架构 §2.3 LangSmith/MCP · §2.4 Pydantic

---

## 0. 第一性原理（项目锚点）

> 内容价值 ≈ 信息增量 × 品牌信任度。架构服务于 **trust_asset → content/adapt → 发布 → 可见度+转化监测**，而非批量发文。PRD §0、§11。

---

## 1. 总体架构

**前后端分离 + AI-Native。** 单体 FastAPI + 模块化目录（MVP 不过早微服务）。

```
apps/web          Vue3
apps/api          FastAPI
packages/agents   Orchestrator(jobs), **graphs(LangGraph)**, **harness(ReAct)**, Review
packages/mcp          geo-mcp-server（P1，只读 tools）
packages/llm      gateway + engine adapters
packages/skills   平台 + beauty_local
packages/industry beauty_local/
infra             Docker Compose
```

### 1.1 分层

```
Presentation  → Vue3 + Pinia（**三舱**：onboarding / strategy-pack / outcomes）
Gateway       → JWT / tenant / 限流
Business      → tenant-svc, kb-svc, **strategy-pack-svc**, content-svc, publish-svc, monitor-svc, **outcome-svc**
AI            → Orchestrator(jobs), **LangGraph subgraphs**, **ReAct Harness**, SkillRuntime, LLM Gateway
Data          → PG, Redis, Celery, OSS/MinIO, Faiss, embedding API
```

---

## 2. 技术选型（定稿 · MVP 可上线）

| 模块 | 选型 | 版本/说明 |
|------|------|-----------|
| **前端** | Vue 3 + **Vite** + **TypeScript** + Element Plus + Pinia | 三舱 SPA |
| **后端** | **Python 3.11+** + FastAPI + Pydantic v2 + Uvicorn | 单体模块化 |
| **DB** | **PostgreSQL 15+** | JSONB(Strategy)；租户 `tenant_id` 全链路 |
| **缓存/队列** | **Redis 7** + **Celery** + Celery Beat | 长任务、weekly monitor |
| **对象存储** | 开发 **MinIO** → 生产 **阿里云 OSS** | 托管页、Faiss 索引、SEMI 导出 |
| **向量** | **Faiss** + **通义/豆包 Embedding API** | per-tenant；MVP 聚类 |
| **LLM** | **packages/llm/gateway** + 4 EngineAdapter | 豆包/DeepSeek/Kimi/文心 |
| **Agent** | **LangGraph** 子图 + **ReAct Harness** | 见 §2.1；**不**替代 L1 jobs |
| **宏编排** | **jobs 表状态机** + Celery task | AWAIT_STRATEGY_PACK 等人机闸门 |
| **部署** | **Docker Compose** → 阿里云 ECS + RDS + Redis 云版 | MVP 不上 K8s |
| **可观测** | **Sentry** + **LangSmith** + JSON 日志 + `/health` | 见 §2.3 |
| **MCP** | **geo-mcp-server**（只读工具暴露） | MVP P1；见 §2.3 |
| **API 校验** | **Pydantic v2 全量** | 见 §2.4；**必须** |

**MVP 刻意不上：** K8s、Milvus/Qdrant、LangGraph **全盘替代** Orchestrator、LangChain 重型链。

### 2.3 LangSmith 与 MCP Server

#### LangSmith（LLM/Agent 追踪 · MVP P0 接入）

| 用途 | 说明 |
|------|------|
| **Trace** | LangGraph 子图、ReAct 每步、LLM Gateway 调用自动上报 span |
| **Debug** | 开发/Staging 看 prompt、tool input/output、latency |
| **Eval** | competitor/gap 图 fixture → LangSmith Dataset → 回归跑分（CI 可选） |
| **与 agent_traces 分工** | LangSmith=运维/研发调试；**agent_traces 表**=租户审计与产品侧追溯（生产必留） |

**接入（Harness / LangGraph 统一）：**

```bash
# .env（staging/prod 可选；dev 建议开）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=geo-{env}          # geo-dev | geo-staging | geo-prod
LANGSMITH_API_KEY=lsv2_...
```

```python
# packages/agents/harness/langgraph_runner.py
# LangGraph compile 时 LangSmith 自动继承环境变量
# 额外 metadata：tenant_id, job_id, graph_name（禁止含 PII 正文）

with tracing_context(metadata={"tenant_id": tid, "job_id": jid}):
    graph.invoke(state)
```

| 环境 | LangSmith |
|------|-----------|
| dev | ✅ 全开 |
| staging | ✅ 全开 |
| prod | ✅ trace 采样（如 10%）+ 禁传 RawInputs 全文 |

**不替代：** Sentry（异常）、业务 metrics（monitor_runs）。

#### MCP Server（Model Context Protocol · MVP P1）

**定位：** 把 GEO **只读能力** 以标准 MCP 工具暴露，供 Cursor/外部 Agent 调用；与 ReAct Harness **共用 Tool 实现**。

```
packages/mcp/
├── server.py              # FastMCP / mcp SDK
├── tools/
│   ├── kb_fetch.py        # 只读 Fact
│   ├── kb_freshness.py
│   ├── diagnose_stats.py  # 最近 source_diagnose 摘要
│   └── engine_probe.py    # 单条探测（配额）
└── auth.py                # API Key → tenant_id
```

| 工具 | MCP 暴露 | Harness 内部 |
|------|:--------:|:------------:|
| kb_fetch | ✅ P1 | ✅ |
| engine_probe | ✅ P1 | ✅ |
| kb_thickness | ✅ P1 | ✅ |
| write_fact / publish | ❌ 禁止 | ❌ |

**部署：** 独立进程 `geo-mcp`（Compose 可选服务）或 FastAPI 子路由 `/mcp`（SSE transport）。

**版本：** MVP 主产品 **不依赖** MCP；P1 交付便于你们用 Cursor 调试 KB/探测。  
**V1.1：** Harness ToolRegistry 与 MCP tools **同一 registry 注册**，避免双份实现。

---

### 2.4 FastAPI + Pydantic v2 校验（必须 · 全量）

**结论：要加，且 MVP 全接口必须使用 Pydantic v2 Models，不用裸 dict。**

| 层级 | 路径 | 校验什么 |
|------|------|----------|
| **API 入参/出参** | `apps/api/schemas/` | 所有 Router Request/Response |
| **三舱契约** | `strategy_pack.py` | `StrategyPackDraft`, `StrategyPackConfirm` |
| **Skill I/O** | `packages/skills/schemas/` | 每个 Skill input/output JSON Schema → Pydantic |
| **LLM 结构化输出** | Skill 内 | LLM 返回 JSON → `model_validate`；失败重试 1 次 |
| **DB 边界** | service 层 | ORM → Pydantic 再返回，不直接暴露 ORM |

**示例：**

```python
# apps/api/schemas/strategy_pack.py
class StrategyPackConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selected_persona_ids: list[str] = Field(min_length=1, max_length=2)
    selected_scenario_ids: list[str] = Field(min_length=1, max_length=5)
    differentiation_brief: list[DifferentiationBrief]
    source_weight_plan: list[SourceWeightChannel]
```

```python
# apps/api/main.py
app = FastAPI(
    title="GEO API",
    # 自动生成 OpenAPI → 前端 openapi-typescript
)
@router.post("/strategy-pack/confirm", response_model=StrategyConfirmResponse)
async def confirm(body: StrategyPackConfirm, tenant: Tenant = Depends(require_tenant)):
    ...
```

| 规则 | 说明 |
|------|------|
| `extra="forbid"` | 策略/Skill 相关 model 禁止未声明字段（防注入） |
| Field 约束 | 篇数≤5、字符串长度、enum channel/skill |
| 统一异常 | `RequestValidationError` → 422 标准 JSON |
| OpenAPI | 前端 Pinia 类型与后端 **同源生成**（可选 openapi-ts） |

**与 LangChain 的关系：** LangChain Message/Tool 用 langchain-core；**业务 API 与 Skill 边界只用 Pydantic v2**，不混用 BaseModel 版本。

---

### 2.2 部署拓扑（Docker Compose · MVP）

```yaml
# infra/docker-compose.yml 服务
services:
  web:        # Nginx + Vue 静态
  api:        # FastAPI + Uvicorn
  worker:     # Celery worker ×2（Skill + LangGraph + diagnose）
  beat:       # Celery Beat（weekly monitor）
  postgres:   # 15+（生产换 RDS）
  redis:      # 7（队列 + 缓存；生产换云 Redis）
  minio:      # 开发 OSS；生产换阿里云 OSS 仅改 env
```

| 环境 | 说明 |
|------|------|
| 开发 | 单机 Compose，MinIO 本地 |
| 生产 | ECS App 机（web+api+worker）+ RDS + Redis 云版 + OSS |

---

## 2.1 Agent 运行时：LangGraph + ReAct + Harness（MVP P0）

> **三层分工：** L1 jobs 宏编排 → L2 LangGraph 分析子图 → L3 ReAct Harness 图内推理+工具。

### 2.1.0 Agent ToB 对标（K博三层 · 简洁）

| 层 | 含义 | GEO 落点 | 状态 |
|----|------|----------|------|
| **L1 通用 LLM** | 入场券 | `packages/llm/gateway` + 4 EngineAdapter | MVP |
| **L2 通用 Harness** | 调度/工具/记忆 | jobs + LangGraph 子图 + ReAct Harness | MVP |
| **L3 垂域 Harness** | **壁垒** | `industry_pack` + Skill + KB 三层 + fact_verify/合规 + 三舱流程 | MVP 生美；B2B V2 |

| 热词 | GEO 做法 |
|------|----------|
| **Skill** | 平台+行业 Skill 清单；喂厚 L3 |
| **Agentic RAG** | 仅 competitor/gap **ReAct 子图**；正文 **kb_fetch 固定链** |
| **蒸馏/自进化** | **V2+** §11.8；先偏好画像，后可选蒸馏；**不跨租户、不自动改 Fact** |

---

```
L1 宏编排   jobs + Celery          onboarding → AWAIT_STRATEGY_PACK → EXECUTE → PUBLISH
L2 子图     LangGraph StateGraph   onboarding / competitor / gap_analyze
L3 执行器   ReAct Harness          Thought → Action(tool) → Observation（有步数上限）
```

| 层 | 职责 | MVP 不用 Agent 的地方 |
|----|------|------------------------|
| L1 | 长流程、等人确认、重试、计费 | — |
| L2 | 分析类分支/并行/checkpoint | 正文 Skill、publish、monitor 批跑 |
| L3 | 多步调 KB/探测/抓页 | fact_verify 规则链、合规 |

**铁律：** Agent **只出草案**；写入 Fact / 发布 / 生成正文须 **方案包或草稿审** 闸门。

### 2.1.2 目录

```
packages/agents/
├── orchestrator/          # jobs 状态机、Celery task 入口
├── graphs/
│   ├── onboarding_graph.py    # 线性：DIAGNOSE→PAIN→PERSONA→COMPETITOR
│   ├── competitor_graph.py    # 条件边 + 内层 ReAct
│   └── gap_analyze_graph.py   # ReAct：KB+diagnose→content_gaps[]
├── harness/
│   ├── tool_registry.py       # 工具注册、tenant 隔离
│   ├── react_harness.py       # ReAct 循环 max_steps
│   ├── langgraph_runner.py    # 统一 checkpoint / trace
│   └── human_gate.py          # interrupt → 对齐 AWAIT_*
└── review/
packages/agents/harness/tools/
  kb_fetch, kb_thickness, engine_probe, page_fetch, faiss_search, fact_check_readonly
```

### 2.1.3 MVP LangGraph 子图

| 子图 | 类型 | 节点/工具 | 触发 |
|------|------|-----------|------|
| **onboarding_graph** | 线性 LangGraph | diagnose → pain → persona → competitor | `POST onboarding/run` |
| **competitor_graph** | 条件边 + **ReAct** | `engine_probe(compare)` → `page_fetch?` → `synthesize_draft` | COMPETITOR_ANALYZE job |
| **gap_analyze_graph** | **ReAct** | `kb_fetch` → `kb_thickness` → `diagnose_stats` → `suggest_gaps` | 方案包 confirm 前 GAP_ANALYZE |

**persona_analyze：** MVP 默认 **单 LLM 节点**（图内一节点）；RawInputs 过少时可加条件边「追问问卷」。

### 2.1.4 ReAct Harness 契约

```python
class ReActHarness:
    max_steps: int = 8                    # competitor 默认 8，gap 默认 6
    tools: list[str]                      # 白名单，禁止 write_fact
    on_step: Callable → agent_traces 表   # thought, action, observation, latency

# 禁止工具（MVP）
FORBIDDEN = ["write_fact", "publish", "auto_confirm_strategy"]
```

### 2.1.5 与 jobs 对接

```
jobs.step = COMPETITOR_ANALYZE
  → LangGraphRunner.run("competitor_graph", {tenant_id, kb, competitors})
  → 写 competitor_analyses JSONB + merge strategy_pack_draft
  → jobs.step = AWAIT_STRATEGY_PACK

jobs.step = GAP_ANALYZE
  → ReActHarness.run("gap_analyze_graph", tools=[kb_fetch, kb_thickness, ...])
  → content_gaps[] → 方案包 C/D 区
```

**onboarding/run：** 整体跑 `onboarding_graph`，节点 checkpoint → SSE 进度 0→100%。

### 2.1.6 正文生成 **不用** LangGraph/ReAct

```
content_unit → SkillRuntime：kb_fetch → LLM → schema validate → fact_verify
```

V1.1 **hybrid_retrieve** 可用 **受限 ReAct**（max 3 步，只读工具），仍不写入 Fact。

### 2.1.7 agent_traces 表（Harness 审计）

| 字段 | 说明 |
|------|------|
| job_id, graph_name, step_idx | 关联 |
| thought, action, action_input, observation | ReAct 步 |
| tokens, latency_ms | 成本 |

**Eval harness（CI）：** `tests/fixtures/beauty/` + 跑 competitor_graph / gap_graph → 断言 schema。

### 2.1.8 依赖

```
langgraph>=0.2
langchain-core   # Message/Tool 抽象 only
langsmith>=0.1   # trace + eval（§2.3）
celery[redis]
pydantic>=2.0    # API + Skill I/O（§2.4）
# mcp SDK        # P1 geo-mcp-server（§2.3）
```

---

## 3. 三舱展现层架构（MVP P0）

> PRD §2。后端 job 管道不变；前端按舱聚合；**2 次用户闸门**：方案包确认 + 草稿审。

### 3.1 前端模块

```
apps/web/src/
├── views/
│   ├── onboarding/          # 舱1 开店向导
│   ├── strategy-pack/       # 舱2 方案包 + 草稿列表
│   └── outcomes/            # 舱3 效果舱
├── stores/
│   ├── onboarding.ts
│   ├── strategyPack.ts
│   └── outcomes.ts
└── components/
    ├── StrategyPackBlocks/  # A画像 B差异 C场景 D渠道 E展开
    └── DraftReviewList/
```

### 3.2 后端模块

```
apps/api/routers/
├── onboarding.py      # POST run, GET status (SSE)
├── strategy_pack.py   # GET draft, POST confirm
├── content_drafts.py  # GET list, POST bulk-approve
└── outcomes.py        # GET dashboard aggregate

apps/api/services/
├── strategy_pack_builder.py   # 聚合 diagnose/persona/competitor/pain/weight
├── onboarding_pipeline.py     # 调用 onboarding_graph（LangGraph）
└── outcome_aggregator.py      # monitor + hosted_stats + publish_summary
```

### 3.3 onboarding job 链（舱1 · LangGraph onboarding_graph）

```
POST /onboarding/run
  → Celery: LangGraphRunner.run("onboarding_graph")
      nodes: SOURCE_DIAGNOSE → PAIN_MINE → PERSONA → COMPETITOR
  → checkpoint 每节点 → SSE progress 0→100%
  → on complete: strategy_pack_draft ready
```

### 3.4 strategy_pack confirm → Orchestrator

```
POST /strategy-pack/confirm (StrategyPackConfirm body)
  → persist user selections → strategies draft row
  → trigger: gap_analyze_graph(ReAct) → PLAN → REVIEW → EXECUTE_SKILLS
  → skip separate AWAIT_STRATEGY_DIRECTION / AWAIT_SOURCE_WEIGHT / AWAIT_STRATEGY_CONFIRM
    （用户已在方案包一次确认）
  → on EXECUTE done: redirect client to drafts tab
  → AWAIT_CONTENT_REVIEW（草稿审，第二次闸门）
```

### 3.5 Orchestrator 状态（三舱对齐版）

```
KB_READY / ONBOARDING_COMPLETE
  → LOAD_INDUSTRY_PACK
  → [onboarding_graph] → AWAIT_STRATEGY_PACK
  → GAP_ANALYZE（gap_analyze_graph · ReAct）
  → PLAN
  → REVIEW_COMPLIANCE + REVIEW_FACT
  → EXECUTE_SKILLS
  → AWAIT_CONTENT_REVIEW         # 草稿审
  → PUBLISH
  → MONITOR_24H
```

**专家模式（可选）：** 保留 `AWAIT_STRATEGY_DIRECTION` 细分状态，供内部/debug；MVP 默认走路径 above。

---

## 4. Orchestrator 工作流（MVP jobs · 与 §3.5 一致）

```
KB_READY
  → LOAD_INDUSTRY_PACK
  → SOURCE_DIAGNOSE
  → PAIN_MINE + KEYWORD_MINE   # embedding + Faiss + SEO API
  → PERSONA_ANALYZE            # buyer_personas + content_layout_plan
  → COMPETITOR_ANALYZE         # competitor_graph · ReAct
  → AWAIT_STRATEGY_PACK
  → GAP_ANALYZE                # gap_analyze_graph · ReAct
  → PLAN(content_units per article_count, engine_plan, source_weight_plan, monitor_plan)
  → REVIEW_COMPLIANCE + REVIEW_FACT
  → EXECUTE_SKILLS (parallel per content_unit)   # 方案包 confirm 后直接执行；无单独 STRATEGY_CONFIRM
  → AWAIT_CONTENT_REVIEW
  → PUBLISH
  → MONITOR_24H
```

每步写 `jobs` 表；失败可重试；SSE 可选推送进度。

---

## 5. Skill 运行时

```yaml
skill:
  name: beauty_xhs_note
  industry: beauty_local
  tools: [kb_fetch, fact_verify]
  prompt: Layer1 + Layer2(industry) + Layer3(KB)
  input: { content_unit_id, fact_refs, persona_tone, topic_angle }
  output: { title, body, tags, cover_hint, fact_refs }
  constraints: [no_hallucination, compliance_beauty]
```

```python
invoke_skill(name, tenant_id, params, strategy_id)
  → load pack → kb_fetch → LLM → schema validate
  → fact_verify → compliance → SkillResult
```

正文事实见 **§6a kb_fetch**；V1.1 可选 hybrid_retrieve enrich Layer3。

**与 Agent 边界：** Skill **固定链、无 ReAct**；分析走 §2.1 LangGraph。

---

## 6. 探测 Prompt 与信源 API

### 5.1 probe_prompt_builder

```python
templates = load("industry/beauty_local/engines.json")
slots = { city, brand, services[], competitors[] } from KB
prompts = fill_templates(templates, slots)
prompts += llm_expand(prompts, n=3)
return dedupe(prompts)[:10]  # per engine
```

### 5.2 EngineAdapter（联网测信源）

```python
class EngineAdapter(Protocol):
    async def query_with_search(prompt: str) -> EngineResponse

# 实现: DoubaoAdapter, DeepSeekAdapter, KimiAdapter, WenxinAdapter

async def query_with_search(prompt):
    resp = await httpx.post(VENDOR_CHAT_URL, json={
        "model": cfg.model,
        "messages": [{"role":"user","content": prompt}],
        "enable_search": True,   # 或 plugins/bot_id，按厂商文档
    }, headers={"Authorization": f"Bearer {cfg.api_key}"})
    return EngineResponse(
        answer=resp["choices"][0]["message"]["content"],
        citations=parse_citations(resp),  # citations / search_results / refs
    )
```

**说明：** 测信源 = **调 AI 厂商 API 开联网**，从返回 **引用列表** 统计平台；不是自建爬虫抓 SERP。

`citation_parser`: URL → domain → 平台标签（xhs/dianping/zhihu/media/map）

**monitor_run** 与 **source_diagnose** 共用 EngineAdapter，参数一致。

### 5.3 Probe 池

diagnose 高引用问法 + 每周 LLM 轮换 ≤10/engine。

---

### 6.1 FAQs[] 表

| 字段 | 说明 |
|------|------|
| question, answer | 结构化 Q/A |
| fact_refs[] | 必填 |
| source | manual \| imported_raw \| generated |
| status | draft \| published |
| content_asset_id | 可选，关联托管页 |

content_faq：优先 `kb_fetch(faqs)`；生成后 `faq_writeback` 需用户确认。

---

### 6.2 KB 新鲜度

```python
# 任意 KB CRUD 后
async def bump_kb_updated_at(tenant_id):
    await db.execute("UPDATE tenants SET kb_updated_at=now() WHERE id=$1", tenant_id)

@router.get("/tenants/{id}/kb/freshness")
async def kb_freshness(tenant_id):
    t = await get_tenant(tenant_id)
    last_dx = await last_source_diagnose_at(tenant_id)
    last_st = await last_strategy_at(tenant_id)
    return {
        "kb_updated_at": t.kb_updated_at,
        "last_diagnose_at": last_dx,
        "last_strategy_at": last_st,
        "changed_since_diagnose": t.kb_updated_at > last_dx if last_dx else False,
        "changed_since_strategy": t.kb_updated_at > last_st if last_st else False,
    }
```

**前端：** 方案包 E 区 InfoBanner；confirm 前再次拉取。

---

## 7. Faiss 聚类服务（MVP）

```python
class FaissClusterService:
    """per-tenant IndexFlatIP；pain/keyword 共用"""
    def merge_similar(self, tenant_id, vectors, texts, threshold=0.85):
        index = load_or_create(tenant_id)
        # add vectors → search neighbors → merge clusters
        return clusters

# beauty_pain_mine / keyword_mine:
# exact_dedupe → embed(texts) → faiss.merge → llm_name_clusters(edges_only)
#
# ⚠️ MVP Faiss 仅用于上列聚类，不用于正文生成检索。
```

---

## 7a. KB 取数：kb_fetch 与 hybrid_retrieve

### 7a.1 为何 MVP 用 kb_fetch（按 ID），不是向量搜？

| 目标 | kb_fetch | 向量全库搜 |
|------|----------|------------|
| 事实可追溯 | ✅ fact_refs → 审计链 | ⚠️ top-k 不稳定 |
| fact_verify | ✅ 对照固定 ID | ⚠️ 检索漂移 |
| 零幻觉 | ✅ 边界清晰 | ⚠️ 易混入 Signal/噪声 |

**「不全」：** Orchestrator 为 scenario 绑定多条 fact_refs；M5 Review 检依据。  
**「过时」：** `tenants.kb_updated_at` + `GET /kb/freshness`；策略页黄条，用户决定是否继续。

### 7a.2 kb_fetch 接口

```python
def kb_fetch(tenant_id: str, fact_refs: list[str]) -> KbSnapshot:
    """按 ID 拉 Fact 层。ref 格式: brand:1 | store:01 | service:03 | case:02 | faq:12 | competitor:01"""
    return {
        "brand": ..., "stores": [...], "services": [...],
        "cases": [...], "faqs": [...], "competitors": [...],
        "fetched_at": iso8601, "kb_revision": tenant.kb_revision,
    }
```

### 7a.3 V1.1 hybrid_retrieve（Retrieve-Augment，非 Agentic RAG）

```python
class HybridRetrieveService:
    """Faiss 语义 + KeywordLibrary BM25；索引 per-tenant，按 doc_type 分字段"""

    INDEX_TYPES = ("raw_input", "faq", "service", "case")  # Fact 摘要 + Signal 片段

    def retrieve(self, tenant_id, query: str, top_k=5) -> list[RetrievalHit]:
        vec_hits = faiss_search(embed(query), index, top_k)
        kw_hits = bm25_search(keyword_library.confirmed, query, top_k)
        return rrf_merge(vec_hits, kw_hits)  # 每条: {source_id, doc_type, snippet, score}

# Skill 生成链（V1.1）:
#   snapshot = kb_fetch(fact_refs)           # P0 主事实，必走
#   hits = hybrid_retrieve(scenario)         # P1  enrich，可选
#   layer3 = merge(snapshot, hits_for_variants_only)
#   llm_generate(layer1, layer2, layer3)
#   fact_verify against snapshot.fact_refs   # 检索句不得引入未引用新事实
```

**检索内容对照表：**

| 检索源 | doc_type | 用途 | 进正文条件 |
|--------|----------|------|------------|
| RawInputs 片段 | raw_input | 用户原话、variants | 引述；无新价格/NAP |
| FAQs[] | faq | 上下文、fact_refs 候选 | 已在 fact_refs 或升格后 |
| Services 摘要 | service | 项目细节 | 已在 fact_refs |
| Cases | case | 案例句 | 已在 fact_refs |
| KeywordLibrary.confirmed | —（BM25） | keyword_slots | 用户已确认 |
| diagnose 问法 | — | Probe/variants 提案 | 确认后进词库 |

**明确不检索：** Layer1/2 Prompt 模板、外部网页、未确认 External、未确认关键词。

**Agentic RAG：** MVP/V1.1 默认生成路径 **不使用**；V2 仅 `gap_analyze` 等策略辅助可有限多步检索，产出草案须人确认。

```python
invoke_skill(name, tenant_id, params, strategy_id)
  → load pack → kb_fetch → [V1.1: hybrid_retrieve] → LLM → schema validate
  → fact_verify → compliance → SkillResult
```

---

## 7b. source_weight_plan Schema

```json
{
  "engine": "doubao",
  "channels": [
    {
      "channel": "xiaohongshu",
      "cite_share": 0.35,
      "weight": 0.40,
      "article_count": 3,
      "default_skill": "beauty_xhs_note",
      "publish_mode": "SEMI"
    },
    {
      "channel": "hosted_page",
      "cite_share": 0.12,
      "weight": 0.25,
      "article_count": 2,
      "default_skill": "content_faq",
      "publish_mode": "AUTO"
    }
  ]
}
```

`source_weight_builder.py`：读 `source_diagnoses.payload.platform_stats` → 渠道映射表（行业包 `channels.json`）。

---

## 8. content_unit Schema

```json
{
  "id": "cu_001",
  "core_intent": "pain",
  "scenario": "敏感肌能不能做皮肤管理",
  "topic_angle": "专业科普",
  "target_persona": "hesitant_new",
  "variants": ["..."],
  "fact_refs": ["service:03", "raw:08"],
  "engine_targets": ["doubao"],
  "monitor_phrase": "敏感肌 皮肤管理",
  "output": {
    "skill": "beauty_xhs_note",
    "channel": "xiaohongshu",
    "publish_mode": "SEMI",
    "keyword_slots": ["title", "summary"]
  }
}
```

---

## 9. 审核流水线

```
ContentAsset created
  → ReviewPipeline:
      fact_verify      → fact_report
      compliance_check → ad_law_report
      beauty_compliance→ industry_report
      keyword_lint     → stuffing_report
      dss_score (P1)   → dss_report
  → merge → machine_review JSON on asset
  → UI: human approve → status=ready
```

**fact_verify 逻辑：** 抽取数值/实体 → 匹配 KB Fact → 无 match 则 fail。

---

## 10. 发布适配器

```python
class PublishAdapter(Protocol):
    async def publish(asset, credentials) -> PublishResult

class XhsAdapter:
    async def publish(...):
        try: auto_post(...)
        except: return PublishResult(fallback="semi", export_bundle=...)
```

凭证：`tenant_channel_credentials` 表，AES 加密；OAuth 优先。

---

## 11. 监测引擎

```python
class MonitorScheduler:
    def run_weekly(tenant_id):
        core = profile.core_prompts
        probe = profile.probe_prompts[:10]
        for engine in target_engines:
            for pool, prompts in [("core", core), ("probe", probe)]:
                results = call_ai(engine, prompts)
                store(pool, results)
        check_thresholds(core_only=True)
        probe_expansion_proposals()
```

**指标字段：** mention_rate, source_exposure_rate, visibility_count, citation_count, rank, sentiment

---

## 12. 行业包 beauty_local

```
industry/beauty_local/
├── schema.json
├── engines.json          # 探测模板
├── channels.json         # diagnose 域名→渠道映射 + 默认 Skill
├── personas.json         # 3 预置 persona
├── prompts/
├── skills.manifest.json
├── compliance/general_beauty.txt
├── monitor/prompt_templates.json
└── export/
```

**Loader：** 租户 `industry_pack=beauty_local` → 启动时加载 Redis 缓存。

---

## 13. 核心表

| 表 | 关键字段 |
|----|---------|
| tenants | industry_pack, **kb_updated_at** |
| faqs | question, answer, fact_refs, source, status |
| keywords | type, phrase, status, pool_hint |
| source_diagnoses | engine, payload JSONB |
| strategies | payload(content_units, source_weight_plan, buyer_personas, content_layout_plan, …), status |
| strategy_pack_drafts | tenant_id, payload JSONB（聚合草案）, job_id, expires_at |
| hosted_page_events | asset_id, event, ts（效果舱 PV/表单） |
| content_assets | fact_refs, machine_review, status |
| publish_tasks | channel, mode, status, fallback_semi |
| monitor_profiles | core_prompts, probe_prompts, thresholds JSONB |
| monitor_runs | pool, engine, metrics JSONB |
| channel_credentials | channel, encrypted_token |
| **agent_traces** | job_id, graph_name, step_idx, thought, action, observation, tokens, latency_ms |
| competitor_analyses | tenant_id, payload JSONB |

---

## 13b. 二期架构（V1.1 / V2 · MVP 后）

### 13b.1 trust_asset 产线（V1.1+）

```yaml
trust_asset:
  types: [case_study, value_prop, deep_faq]
  status: draft | confirmed
  fact_refs: [...]
  payload: {...}   # 结构化案例/话术/问答
```

```
trust_asset Skill → fact_verify → user confirm → Cases[] / FAQs[] / trust_assets 表
content_unit.fact_refs 可指向 trust_asset_id
```

Skills（规划）：`case_builder`, `spec_to_value`（V2 B2B）, `faq_from_raw`

### 13b.2 adapt_engine 一源多态（V2 · B2B）

```python
class AdaptEngine:
    """core_material 扇出多形态；每条独立 content_unit + Skill"""

    ADAPTERS = {
        "long_form": "b2b_long_article",      # 公众号/媒体
        "video_script": "b2b_video_script",   # 1-3min 脚本
        "short_copy": "beauty_xhs_note",      # 短文案（生美复用）
        "sales_points": "b2b_sales_sheet",    # 私信/线下卖点
    }

    def fan_out(core_material_id, channels: list[str]) -> list[ContentUnit]:
        base = load_core_material(core_material_id)  # 同一 fact_refs
        return [content_unit(adapter, base.fact_refs, persona_tone=...) for ...]
```

约束：派生内容 **不得新增 fact**；fact_verify 对照 `core_material.fact_refs`。

### 13b.3 persona / 竞品（MVP · LangGraph · V2 深化）

MVP 经 **§2.1 LangGraph 子图** 实现（非独立脚本）：

```
onboarding_graph 内含 persona 节点 → buyer_personas[] + content_layout_plan[]
competitor_graph（ReAct）→ competitor_topics[] + differentiation_brief[] 草案
```

**V2 B2B：** 采购决策链多角色；竞品大规模定向采集。

### 13b.4 转化追踪（V1.1 简化 → V2 完整）

**表（V1.1）：**

| 表 | 字段 |
|----|------|
| consult_logs | tenant_id, date, channel, note, related_asset_id, source_hint |
| page_events | asset_id, event(pview/form_submit), ts（托管页第一方） |

**归因（V1.1）：** `publish_tasks.utm_content=asset_id` + 7 天窗口 + ConsultLog 手工关联。

**V2：** 渠道 API 拉取阅读/互动；CRM Webhook；Dashboard 漏斗（可见度→流量→咨询→成交）。

### 13b.5 监测→偏好学习 / 蒸馏（V2+ · 越用越懂行）

> **原则：** 学 **偏好与策略**，不学 **事实**；Fact 仍只来自 KB + 人确认。

**数据从哪来：**

```
monitor_runs（提及/露出/scenario 答对率）
+ consult_logs / page_events（咨询、表单）
+ 方案包用户删改、草稿 diff、批量驳回原因
  → weekly feedback_aggregator job
  → tenant_preference_proposal（草案，JSONB）
  → 效果舱 [采纳优化建议]（人确认，非自动生效）
```

**三阶段（由轻到重）：**

| 阶段 | 做什么 | 改什么 | 合规 |
|------|--------|--------|------|
| **V2a 偏好画像** | 统计高转化 scenario/渠道/persona/topic_angle | Orchestrator **排序权重**、source_weight 初值、Probe 轮换 | 租户隔离；可一键重置 |
| **V2b 检索/排序增强** | 成功案例写入 `preference_examples[]` | Faiss **rerank**、hybrid_retrieve 加权；**不改 LLM 权重** | 仅本租户数据；脱敏 PII |
| **V2c 可选蒸馏** | `(scenario, fact_refs, 用户审定稿)` 对 | 行业包 **语气/体例** 小适配器或 prompt 槽；**禁止蒸馏价格/NAP/参数** | 租户 **opt-in**；平台发版；抽样人工 audit |

**明确不做：**

- 用监测数据 **自动 fine-tune 主模型** 或 **自动写 KB**
- **跨租户** 联合训练
- 未经确认的 **自动改策略/自动发布**

**表（V2+）：**

| 表 | 用途 |
|----|------|
| feedback_events | 原始信号（monitor/consult/edit/reject） |
| tenant_preference_profiles | 已确认偏好（ranking_weights, favored_scenarios, tone_hints） |
| preference_proposals | 待采纳草案 + diff 说明 |
| distillation_batches | V2c 训练批次、opt-in、audit 状态（可选） |

---

## 14. 演进

| 阶段 | 变化 |
|------|------|
| **MVP** | 单体 Compose + **jobs + LangGraph 子图 + ReAct Harness** + Celery + 三舱 UX + Faiss + kb_fetch + Core/Probe |
| **V1.1** | hybrid_retrieve、trust_asset、scenario-first Core、KB gap、ConsultLog |
| **V2 二期** | adapt_engine、B2B 包、完整转化 Dashboard、**V2a 偏好画像** |
| **V2+** | **V2b 检索 rerank · V2c 可选蒸馏**（opt-in，§13b.5） |

---

*架构设计 v2.5*
