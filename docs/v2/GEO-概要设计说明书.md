# GEO 智能品牌平台 — 概要设计说明书 v2

> **版本**：V2.5 | **日期**：2026-07-04 | **关联**：PRD-v3.md · 架构 §2.3～§2.4

---

## 0. 第一性原理（项目锚点）

> 特定人群 × 真实场景 × 信息增量 × 差异化 × 专业信任 → **咨询/转化**。  
> 不以发文篇数为 North Star；拒绝批量伪原创与一稿通发。详见 PRD §0。

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **第一性原理** | 信任资产 → 可见度 → 转化；见 §0 |
| KB 为本 | 发布事实唯一权威；Fact/Signal/External |
| 先选 AI 再测信源 | TargetEngines → source_diagnose |
| content_unit | 场景问题 + persona + topic_angle + 多形态 |
| 双池监测 | Core 稳定 KPI；Probe 探索扩词 |
| Skill 为本 | 平台 Skill + 行业包；不按企业复制 |
| 人必确认 | 策略方向页、词库、策略、内容、策略更新草案 |

---

## 2. 四层架构

```
展现层   Vue3+TS 管理台（**三舱**：onboarding / strategy-pack / outcomes）
业务层   FastAPI + Celery（tenant/kb/strategy-pack/content/publish/monitor/outcome）
智能层   **jobs 宏编排** + **LangGraph 子图** + **ReAct Harness** + Skill Runtime + LLM Gateway
数据层   PostgreSQL + Redis + OSS/MinIO + Faiss + embedding API
```

### 2.1 平台横切（MVP）

| 能力 | 结论 | 检测见《实施清单》§3.6 |
|------|------|------------------------|
| **LangSmith** | P0 必接；dev/staging 全量 trace，prod 采样；与 `agent_traces` 双写 | §3.6.1 |
| **Pydantic v2** | P0 **必须**；全 Router + Skill I/O；策略 schema `extra=forbid` | §3.6.2 |
| **geo-mcp-server** | P1 可选；只读 tools，与 Harness ToolRegistry 同源；主产品不依赖 | §3.6.3 |

---

## 3. 模块划分

| 子系统 | 职责 |
|--------|------|
| 用户中心 | 租户/RBAC |
| 知识库中心 | KB CRUD、Fact/Signal 标注、**kb_updated_at / freshness** |
| 策略中心 | diagnose、pain/keyword、**策略方向页**、Orchestrator、Review |
| 内容工厂 | Skill 生成、机器审、人工审 |
| 发布中心 | AUTO/SEMI/GUIDED、降级 |
| 监测中心 | Core+Probe、临界检测 |
| 报告中心 | 策略报告、效果报告 |
| 行业包 | beauty_local |

---

## 3. 展现层：三舱 UX（MVP P0）

> 后端 Orchestrator 步骤不变；展现层按舱合并，减少用户点击。详见 PRD §2。

### 3.1 路由与页面

| 路由 | 舱 | 说明 |
|------|-----|------|
| `/onboarding` | 舱1 懂我 | 开店向导（6 步表单向导） |
| `/strategy-pack` | 舱2 定方案 | 方案包 + 草稿列表（同页上下或 Tab） |
| `/outcomes` | 舱3 出结果 | 效果舱 + 发布状态 + 发布操作 |

**废弃独立 MVP 路由（逻辑内聚方案包）：** `/strategy-direction`、`/source-weight` → 高级模式折叠或 V1.1 专家入口。

### 3.2 舱1 → 舱2 衔接

```
onboarding/run (job)
  → jobs: DIAGNOSE → PAIN → PERSONA → COMPETITOR
  → SSE progress → 100% 跳转 /strategy-pack?draft=1
strategy-pack/draft API 聚合各步 JSON 为 StrategyPackDraft
```

### 3.3 舱2 方案包数据模型

```yaml
StrategyPackDraft:
  buyer_personas: [...]
  content_layout_plan: [...]
  competitor_topics: [...]
  differentiation_brief: [...]
  pain_clusters: [...]          # 带 selected 默认
  campaign_directions: [...]
  source_weight_plan: [...]     # D 区；article_count 默认=len(selected_scenarios)
  keyword_library_draft: [...]  # E 区折叠
  freshness: {...}              # 黄条

StrategyPackConfirm:            # 用户 POST 确认体
  selected_persona_ids: []
  selected_scenario_ids: []
  differentiation_brief: [...]  # 可编辑
  source_weight_plan: [...]     # 可改 weight；article_count 建议只读=场景数
  confirmed_keywords: [...]
```

确认 → Orchestrator：`GAP_ANALYZE → PLAN → REVIEW → AWAIT_STRATEGY_CONFIRM(可跳过若方案包已确认) → EXECUTE_SKILLS`

**MVP 简化：** 方案包 `[确认并生成]` = 同时完成策略确认 + 触发生成（合并原两次闸门为一次，草稿审为第二次）。

### 3.4 舱3 效果舱

```
OutcomeDashboard:
  ai_metrics: from monitor_runs (Core)
  hosted_page_stats: PV/form (第一方)
  publish_summary: 各渠道 published/semi/failed
  consult_logs: V1.1
  strategy_suggestions: gap_analyze 草案入口
```

---

## 4. 知识库中心

### 4.1 实体

Tenant, TargetEngine, Brand, Store, Service, Case, Competitor, **FAQ(Fact)**, RawInput(Signal), Keyword, ExternalCandidate, SourceDiagnosis, Strategy, ContentAsset, PublishTask, MonitorProfile, MonitorRun

### 4.2 主流程（后端 · 用户见三舱）

**用户路径：** 开店向导 → 方案包 → 草稿审 → 效果舱  

**系统管道（与 Orchestrator jobs 一致）：**

```
录入 KB + onboarding/run（**onboarding_graph** LangGraph）
  → competitor 节点内 **competitor_graph** ReAct
  → strategy_pack/draft → 用户 confirm
  → **gap_analyze_graph** ReAct → PLAN → EXECUTE（Skill 固定链，无 ReAct）
  → 草稿审 → ready → Publish → 效果舱
```

**KB 新鲜度：** 任意 KB CRUD 刷新 `tenants.kb_updated_at`；策略方向页加载时 `GET /kb/freshness`，展示上次改动及相对诊断/策略是否过期。

---

## 5. 信源诊断（source_diagnose）

```
1. probe_prompt_builder: engines.json + KB 填槽 → 5-10 条/engine
2. EngineAdapter: POST 各 AI 联网 Chat API → citations[]
3. citation_parser → platform_stats, map_gap
4. 存 SourceDiagnosis；高引用问法 → ExternalCandidates
```

**接入：** 豆包/DeepSeek/Kimi/文心 **官方 API + 联网开关**；平台统一密钥，非租户爬虫。

**渠道计划：** 禁止写死行业表；必须引用诊断结果（例：主攻豆包→小红书/点评）。

---

## 5b. FAQs[]（Fact 层，MVP）

```
录入: 表单 Q/A + fact_refs（manual）
升格: RawInputs 整理 → FAQs[]
生成: content_faq 读 FAQs[] → 审核通过 → 回写 FAQs[]（generated）
发布: publish_website 输出 FAQPage Schema
```

---

## 6. 痛点、词库与策略方向页

### 6.1 beauty_pain_mine / keyword_mine（共用聚类）

```
RawInputs + SEO API + diagnose反推 + 手动
  → exact 去重 → embedding → Faiss 合并（≥0.85, per-tenant）
  → LLM 兜底（簇命名、边缘句）
  → pain_clusters[] + KeywordLibrary draft
```

### 6.2 方案包区块（原策略方向页 + 信源权重 · UI 合并）

| 区块 | 用户输入 | 对应原页面 |
|------|----------|------------|
| A 画像 | 确认 persona + layout_plan | 策略方向·画像 |
| B 差异化 | 确认 differentiation_brief | 策略方向·差异化 |
| C 场景 | 勾选 scenario + campaign | 策略方向·痛点/爆点 |
| D 渠道 | weight + 篇数(=场景数) | 信源权重页 |
| E 展开 | 词库 + freshness 黄条 | 策略方向·词库 |

---

### 6.3 source_weight_builder（逻辑 · 方案包 D 区）

```
source_diagnose.platform_stats
  → source_weight_builder（weight ∝ cite_share；article_count 默认 = len(selected_scenarios)）
  → source_weight_plan[]
```

**Orchestrator 分配逻辑：**

```
total_slots = len(selected_scenarios)   # 默认等于 article_count 总和
topics = campaign(优先) + selected_pains + differentiation
for channel in plan where article_count > 0:
  assign content_units；each: 1 scenario + 1 skill + 1 channel
```

---

## 7. content_unit 与内容工厂

```yaml
content_unit:
  core_intent, scenario, channel, topic_angle, target_persona
  variants[], fact_refs[]
  output: { skill, publish_mode }   # 单渠道单篇
```

**生成链：**

```
MVP:
  kb_fetch(fact_refs) + Layer1/2/3 Prompt → content Skill → 机器审 → draft

V1.1（在 kb_fetch 之后、LLM 之前可选）:
  hybrid_retrieve(scenario) → enrich Layer3（RawInputs 引述 / variants）
  → 仍须 fact_verify 对照 fact_refs
```

**KB 取数说明：** `kb_fetch` 按 ID 拉 Fact，是为 **零幻觉 + 可审计**；「不全」靠 Orchestrator 多绑 refs，「过时」靠 kb_updated_at / freshness；混合检索只 **补表述**，详见 PRD §5.2b、需求规格 §5.0。

**一源多态：** 同一 `fact_refs` 可出现在多个 content_unit（不同渠道/篇位）；每 unit 仅 1 个 `output` Skill。topic_angle 控制切入，persona_tone 控制语气。

---

## 8. 发布中心

```
PublishAdapter:
  HostedPageAdapter    AUTO
  WordPressAdapter     AUTO optional
  XhsAdapter           AUTO, on_fail→ExportAdapter
  ZhihuAdapter         AUTO, on_fail→ExportAdapter
  GuidedAdapter        点评/美团
```

发布任务：draft → ready → publishing → published | failed(SEMI包)

---

## 9. 监测中心

### 9.1 MonitorProfile

```yaml
target_engines: [doubao, deepseek]
core_prompts: from KeywordLibrary.confirmed  # ~20/engine
probe_prompts: agent_generated               # ≤10/engine, weekly rotate
thresholds:
  mention_rate_min: 0.30
  consecutive_weeks: 2
  source_exposure_zero_weeks: 2
```

### 9.2 执行

```
weekly: monitor_run(core) + monitor_run(probe)
post_publish: monitor_run(core subset, +24h)

aggregate → 效果报告
  Core → 主 KPI + 临界检测
  Probe → 探索页 + 扩词提案

if threshold_breach → gap_analyze → StrategyUpdateDraft
```

---

## 10. 数据表（逻辑）

tenants(**kb_updated_at**), brands, stores, services, raw_inputs, keywords, target_engines, source_diagnoses, strategies(JSON: content_units, **source_weight_plan**, campaign_directions, differentiation_brief), content_assets(fact_refs, review_result), publish_tasks, monitor_profiles, monitor_runs(pool: core|probe), jobs, **faiss_indexes**(tenant_id, path)

---

## 11. API 概要

| 方法 | 路径 | 说明 |
|------|------|------|
| CRUD | /api/tenants/{id}/kb/* | 知识库 |
| GET | /api/tenants/{id}/kb/freshness | KB 新鲜度 |
| POST | /api/tenants/{id}/onboarding/run | **舱1** 开店向导 → 异步分析 job 链 |
| GET | /api/tenants/{id}/onboarding/status | job 进度 SSE/轮询 |
| GET | /api/tenants/{id}/strategy-pack/draft | **舱2** 方案包聚合草案 |
| POST | /api/tenants/{id}/strategy-pack/confirm | 确认方案包 → PLAN+EXECUTE |
| GET | /api/tenants/{id}/content-drafts | 草稿列表 + machine_review |
| POST | /api/tenants/{id}/content-drafts/bulk-approve | 批量通过 → ready |
| GET | /api/tenants/{id}/outcomes | **舱3** 效果舱聚合 |
| POST | /api/tenants/{id}/source-diagnose | 诊断（可被 onboarding 调用） |
| POST | /api/tenants/{id}/strategy-direction | 内部/专家模式（可选） |
| POST | /api/tenants/{id}/analyze | Orchestrator 手动触发 |
| CRUD | /api/content-assets | 审核 |
| POST | /api/publish-tasks | 发布 |
| GET | /api/monitor/runs | 监测 |

---

## 12. 安全与异步

JWT+RBAC+tenant 隔离；Skill 禁跨 tenant；爬虫白名单。

Skill/监测/发布：**Redis 队列**异步；Orchestrator MVP 用 jobs 表状态机。

---

## 13. 延后能力

**V1.1：** trust_asset、scenario-first Core、KB gap、ConsultLog、hybrid_retrieve。

**V2 二期：** adapt_engine、B2B 包、完整转化 Dashboard、**V2a 偏好画像**。

**V2+：** **V2b 检索 rerank · V2c 可选蒸馏**（§11.8 / 架构 §13b.5；学偏好不学事实）。

**Agent ToB：** L1 LLM + L2 Harness（LangGraph/ReAct）+ **L3 垂域**（行业包+Skill）；详 PRD §7.1、架构 §2.1.0。

---

*概要设计 v2.5*
