# GEO 实施清单 v2

> **版本**：V2.5 | **日期**：2026-07-04 | **关联**：PRD-v3.md · 架构 §2.3～§2.4

---

## 1. 目标

多企业 GEO SaaS MVP（生美）：**三舱 UX** — 开店向导 → 方案包+草稿审 → 效果舱。  
后端：诊断→画像/竞品→Orchestrator→发布→监测（用户只见 3 步）。

---

## 2. 三舱 vs 系统管道

| 用户舱 | 用户操作 | 系统管道 |
|--------|----------|----------|
| **舱1 懂我** | 开店向导一次提交 → 开始分析 | 建库 + DIAGNOSE + PAIN + PERSONA + COMPETITOR |
| **舱2 定方案** | 方案包确认 → 草稿审 | PLAN + EXECUTE + 机器审 + 人工审 |
| **舱3 出结果** | 发布 + 看效果舱 | PUBLISH + MONITOR + outcomes API |

**用户闸门 2 次：** ① 方案包 `[确认并生成]`  ② 草稿 `[通过]`

---

## 3. 阶段 0：平台基础

| # | 任务 | 优先级 |
|---|------|--------|
| 0.1 | 租户/RBAC/隔离 | P0 |
| 0.2 | Skill 注册+invoke | P0 |
| 0.3 | jobs 异步队列 + **Celery** worker/beat | P0 |
| 0.4 | IndustryPackLoader | P0 |
| 0.5 | Orchestrator jobs + **LangGraphRunner** | P0 |
| 0.6 | **ReActHarness** + ToolRegistry | P0 |
| 0.7 | **agent_traces** 表 | P0 |
| 0.8 | **LangSmith** env + tracing_context | P0 |
| 0.9 | **apps/api/schemas/** Pydantic 骨架 + 422 统一 | P0 |
| 0.10 | 计费骨架 | P1 |

---

## 3.5 阶段 0.5：三舱 UX（P0 · 与后端并行）

| # | 任务 | 验收 |
|---|------|------|
| UX-1 | **开店向导** `/onboarding` + onboarding/run job | 一次提交→进度条→进方案包 |
| UX-2 | **strategy_pack_builder** 聚合 API | GET draft 含 A～E 五块 |
| UX-3 | **方案包页** `/strategy-pack` | 确认并生成→触发 PLAN+EXECUTE |
| UX-4 | **草稿列表** 同页 Tab | 机器审+批量通过 |
| UX-5 | **效果舱** `/outcomes` | AI KPI+托管页 PV+发布状态 |
| UX-6 | Orchestrator `AWAIT_STRATEGY_PACK` | 合并原 3 AWAIT |
| UX-7 | **onboarding_graph** LangGraph | checkpoint+SSE |
| UX-8 | **competitor_graph** ReAct | engine_probe+page_fetch |
| UX-9 | **gap_analyze_graph** ReAct | content_gaps[] |

---

## 3.6 阶段 0.6：LangSmith / Pydantic / MCP 检测（P0/P1）

> 架构 §2.3～§2.4。**结论：LangSmith + Pydantic 必做（P0）；MCP 主产品不依赖（P1）。**

### 3.6.1 LangSmith（P0 · 必接）

| # | 任务 | 检测方法 |
|---|------|----------|
| LS-1 | `.env.example` 含 `LANGCHAIN_TRACING_V2` / `LANGSMITH_API_KEY` / `LANGCHAIN_PROJECT` | 变量齐全 |
| LS-2 | `LangGraphRunner` + LLM Gateway 继承 env | dev 跑 onboarding_graph |
| LS-3 | metadata：`tenant_id`, `job_id`, `graph_name`（**无 PII 正文**） | LangSmith UI 可见 tag |
| LS-4 | prod **采样**（如 10%）配置项 | `LANGSMITH_SAMPLE_RATE` 或等价 |
| LS-5 | **agent_traces 双写**（产品审计不依赖 LangSmith） | DB 有 trace 行 |

**通过标准：** dev 执行一次 `POST onboarding/run` → LangSmith 项目 `geo-dev` 出现 graph span；同 job_id 在 `agent_traces` 可查。

### 3.6.2 FastAPI + Pydantic v2（P0 · 必须全量）

| # | 任务 | 检测方法 |
|---|------|----------|
| PY-1 | 所有 Router 声明 Request/Response Model | 无裸 `dict` 入参/出参 |
| PY-2 | 三舱 schema：`StrategyPackDraft` / `StrategyPackConfirm` 等 | `apps/api/schemas/` 独立文件 |
| PY-3 | 每个 Skill `packages/skills/schemas/` input/output | invoke 前 validate |
| PY-4 | 策略类 Model `extra="forbid"` | 多传字段 → 422 |
| PY-5 | LLM JSON → `model_validate`；失败重试 1 次 | 故意坏 JSON 测重试 |
| PY-6 | `RequestValidationError` → 统一 422 JSON | curl 非法 body |
| PY-7 | `/openapi.json` 可导出 | 前端 openapi-ts 可用（P1） |

**通过标准：** `POST strategy-pack/confirm` 传未知字段 → **422**；合法 body → 200 + 类型正确 Response；OpenAPI 文档与 schema 一致。

### 3.6.3 geo-mcp-server（P1 · 可选延后）

| # | 任务 | 检测方法 |
|---|------|----------|
| MCP-1 | `packages/mcp/server.py` 只读 tools | kb_fetch, diagnose_stats, engine_probe, kb_freshness |
| MCP-2 | 与 Harness **ToolRegistry 同一实现** | 改一处两边生效 |
| MCP-3 | **禁止** write_fact / publish | 工具列表无写操作 |
| MCP-4 | API Key → tenant_id 鉴权 | 跨租户拒绝 |
| MCP-5 | Compose 可选 `geo-mcp` 或 FastAPI `/mcp` SSE | Cursor 连上能 list_tools |

**通过标准：** Cursor MCP 配置连本地 → `list_tools` 仅只读；`kb_fetch` 返回与 API 同源数据；无 publish 类工具。

---

## 4. 阶段 1：知识库

| # | 任务 | 验收 | P |
|---|------|------|---|
| 1.1 | TargetEngines 表单 | 主攻/次攻 | P0 |
| 1.2 | Brand/Store/Service CRUD | NAP 完整 | P0 |
| 1.3 | RawInputs + Signal 标注 | 粘贴可用 | P0 |
| 1.4 | **FAQs[] CRUD** | Q/A/fact_refs | P0 |
| 1.5 | KeywordLibrary UI | Agent+SEO 出词→确认 | P0 |
| 1.6 | **kb_updated_at** + freshness API | 策略页展示 | P0 |
| 1.7 | SeedKeywords | 可选 | P1 |
| 1.8 | 文件上传 | MinIO/本地 | P1 |

---

## 5. 阶段 2：信源诊断

| # | 任务 | 验收 | P |
|---|------|------|---|
| 2.1 | probe_prompt_builder | 模板填槽 5-10/engine | P0 |
| 2.2 | **EngineAdapter** 四引擎联网 API | citations 解析 | P0 |
| 2.3 | source_diagnose Skill | 平台分布+map_gap | P0 |
| 2.4 | 诊断报告页 | 可视化 | P0 |

---

## 6. 阶段 3：痛点+词库

| # | 任务 | 验收 | P |
|---|------|------|---|
| 3.1 | embedding + **Faiss** 聚类服务 | per-tenant index | P0 |
| 3.2 | beauty_pain_mine | pain_clusters | P0 |
| 3.3 | keyword_mine + **SEO API** | 20-40 条草案 | P0 |
| 3.4 | **persona_analyze** | buyer_personas + content_layout_plan | P0 |
| 3.5 | **competitor_content_analyze** | AI 对比探测 + 白名单页抓取 | P0 |
| 3.6 | **方案包 UI**（合并策略方向+信源权重） | A～E 五区块 + source_weight_builder | P0 |

---

## 7. 阶段 4：策略

| # | 任务 | 验收 | P |
|---|------|------|---|
| 4.1 | Orchestrator 按篇数分配 content_unit | 1篇=1渠道1Skill | P0 |
| 4.2 | Review 合规/事实 | 风险标注 | P0 |
| 4.3 | 策略报告可编辑 | 确认闸门 | P0 |
| 4.4 | 虚构品牌拦截 | P0 | P0 |

---

## 8. 阶段 5：内容+审核

| # | 任务 | 验收 | P |
|---|------|------|---|
| 5.1 | content_faq 读 FAQs[] | Schema 托管页 | P0 |
| 5.1b | **FAQ 回写** | 审核后写入 FAQs[] | P0 |
| 5.2 | 小红书/知乎 Skill | fact_refs | P0 |
| 5.3 | fact_verify | A1-A6b 清单 | P0 |
| 5.4 | compliance+beauty | A7-A11 | P0 |
| 5.5 | 内容审核工作台 | draft→ready | P0 |
| 5.6 | dss_score | P1 | P1 |

---

## 9. 阶段 6：发布

| # | 任务 | 验收 | P |
|---|------|------|---|
| 6.1 | 托管页 AUTO+Schema+llms.txt | P0 | P0 |
| 6.2 | 小红书 AUTO+SEMI 降级 | 失败可导出 | P0 |
| 6.3 | 知乎 AUTO+SEMI 降级 | 同上 | P0 |
| 6.4 | GUIDED 点评/美团 | P1 | P1 |
| 6.5 | 凭证加密存储 | P0 | P0 |

---

## 10. 阶段 7：监测

| # | 任务 | 验收 | P |
|---|------|------|---|
| 7.1 | Core 池 monitor_setup | confirmed keywords | P0 |
| 7.2 | Probe 池 ≤10/engine | 单独报表 | P0 |
| 7.3 | 4 引擎 monitor_run | weekly | P0 |
| 7.4 | 24h 发布后复测 | 不触发临界 | P0 |
| 7.5 | 临界检测+策略草案 | 2周规则 | P0 |
| 7.6 | Probe→扩词提案 | UI 提示 | P1 |

---

## 11. 开发顺序

```
1租户 → 2KB+onboarding向导 → 3一键分析(诊断/痛点/画像/竞品)
→ 4方案包+草稿审 → 5Orchestrator → 6内容Skill → 7发布 → 8效果舱
```

**最小闭环：** onboarding向导→一键分析→方案包确认→FAQ+1小红书→托管页→效果舱1轮

---

## 12. MVP 验收清单

- [ ] 多租户 RBAC
- [ ] **三舱 UX**：开店向导 / 方案包 / 效果舱
- [ ] onboarding/run 一键分析 job 链
- [ ] persona + competitor + 方案包 A～E
- [ ] 方案包一次确认 → 批量生成草稿 → 草稿审
- [ ] TargetEngines + RawInputs + FAQs[]
- [ ] Faiss 聚类 + SEO API
- [ ] 机器审+人工审
- [ ] 托管页 AUTO + 小红书/知乎 SEMI 降级
- [ ] Core+Probe 监测 + 效果舱 AI KPI
- [ ] **LangGraph 三子图 + ReActHarness + agent_traces**
- [ ] **LangSmith** trace（dev 全开 + agent_traces 双写）
- [ ] **Pydantic v2** 全路由 + Skill I/O + `extra=forbid` 策略 schema
- [ ] **geo-mcp-server** 只读 MCP（P1 可延后）
- [ ] Celery worker + Beat
- [ ] beauty_local 行业包加载
- [ ] docker-compose 本地一键起

**排除：** 全网负面、Neo4j、完整 CMS、全自动零人工

---

## 13. 开放事项

| # | 任务 | 验收 | 版本 |
|---|------|------|------|
| 10.1 | **hybrid_retrieve 服务** | Faiss+BM25 per-tenant | V1.1 |
| 10.2 | variants / fact_refs 候选 | 检索 enrich Layer3 | V1.1 |

**待定：**

1. 托管页自定义域名 2. 内容条数计费细则 3. SEO API 供应商 4. 定向爬虫(V1.2)

---

## 14. 二期排期（MVP 后 · 不在 MVP 验收内）

### 14.1 V1.1

| # | 任务 | 验收 |
|---|------|------|
| 11.1 | trust_asset 产线 | case_builder / faq_from_raw |
| 11.2 | hybrid_retrieve | Layer3 enrich |
| 11.3 | scenario-first Core 池 | Core=scenario 为主 |
| 11.4 | KB 厚度 + gap | 低分阻断批量生成 |
| 11.5 | ConsultLog | 简化归因 |

### 14.2 V2 二期（B2B）

| # | 任务 | 验收 |
|---|------|------|
| 12.1 | adapt_engine 一源多态 | core_material→4 形态 fan-out |
| 12.2 | B2B 深度内容 Skill | 对比/选型/白皮书 |
| 12.3 | 政策/参数 fact_verify | 行业规则库 |
| 12.4 | 转化 Dashboard | 流量+咨询+漏斗 |
| 12.5 | 行业包 b2b_manufacturing | 加载即用 |
| 12.6 | 竞品大规模定向采集 | 官网/行业媒体 |
| 12.7 | **V2a 偏好画像** | feedback→proposal→采纳→PLAN 排序 |

### 14.3 V2+（偏好 / 蒸馏）

| # | 任务 | 验收 |
|---|------|------|
| 13.1 | feedback_events + weekly aggregator | 信号入库 |
| 13.2 | 效果舱 preference_proposal 采纳 UI | 人确认生效 |
| 13.3 | V2b preference_examples rerank | 本租户 only |
| 13.4 | V2c 蒸馏 opt-in + audit | 仅语气/体例；禁事实 |

---

## 15. infra（P0）

| # | 任务 | 验收 |
|---|------|------|
| I-1 | docker-compose（web/api/worker/beat/pg/redis/minio） | 本地一键起 |
| I-2 | `.env.example` | LLM/OSS/DB/Celery/**LangSmith** 变量 |
| I-3 | Sentry + JSON 日志 | 异常上报 |
| I-4 | **LangSmith** 接入 | 见 §3.6.1 检测 |
| I-5 | **apps/api/schemas/** Pydantic 全路由 | 见 §3.6.2 检测 |
| I-6 | **geo-mcp-server**（P1） | 见 §3.6.3 检测 |

---

*实施清单 v2.5*
