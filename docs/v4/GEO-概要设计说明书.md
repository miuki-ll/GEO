# GEO 智能品牌平台 — 概要设计说明书 v4

> **版本**：V4.1 | **日期**：2026-07-04 | **关联**：PRD-v4.md · GEO-需求规格说明书.md

---

## 0. 第一性原理（项目锚点）

> 特定人群 × 真实场景 × 信息增量 × 差异化 × 专业信任 → **咨询/转化**。  
> 不以发文篇数为 North Star；**scenario 为最小生产单元**。详见 PRD-v4 §0、需求规格 §3 转化闭环。

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **第一性原理** | 信任资产 → 可见度 → 转化闭环；见 §0 |
| KB 为本 | 发布事实唯一权威；Fact/Signal/External |
| scenario-first | 生产与（V1.1）监测以场景问法为主；词库辅助 |
| 先选 AI 再测信源 | TargetEngines → source_diagnose |
| content_unit | 1 scenario + 1 渠道 + 1 Skill |
| 双池监测 | Core 稳定 KPI；Probe 探索扩词 |
| Skill 为本 | 平台 Skill + 行业包；不按企业复制 |
| 人必确认 | 方案包（闸门①）、草稿审（闸门②）、策略更新草案 |
| thin KB 门槛 | ≥2 Services 且 ≥3 FAQs 才可 confirm |
| 视觉方向 | 结论句大字号、卡片化；效果舱偏报告感（非纯后台表格） |

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
| **geo-mcp-server** | P1 可选；只读 tools，与 Harness ToolRegistry 同源 | §3.6.3 |

---

## 3. 模块划分

| 子系统 | 职责 |
|--------|------|
| 用户中心 | 租户/RBAC |
| 知识库中心 | KB CRUD、Fact/Signal 标注、**kb_updated_at / freshness** |
| 策略中心 | diagnose、pain/keyword、**方案包**、Orchestrator、Review |
| 内容工厂 | Skill 生成、机器审、人工审 |
| 发布中心 | AUTO/SEMI/GUIDED、降级、**content_asset_id 追踪** |
| 监测中心 | Core+Probe、临界检测 |
| 报告中心 | 策略报告、效果报告、**迭代草案入口** |
| 行业包 | beauty_local |

---

## 4. 展现层：三舱 UX（MVP P0）

> 后端 Orchestrator 步骤不变；展现层按舱合并。详见 PRD-v4 §2。

### 4.1 路由与页面

| 路由 | 舱 | 说明 |
|------|-----|------|
| `/onboarding` | 舱1 懂我 | 开店向导（6 步表单向导） |
| `/strategy-pack` | 舱2 定方案 | 方案包 + 草稿列表（同页 Tab） |
| `/outcomes` | 舱3 出结果 | 效果舱 + 发布 + 策略建议 |

**废弃独立 MVP 路由：** `/strategy-direction`、`/source-weight` → 内聚方案包；V1.1 可选专家入口。

### 4.2 舱1 → 舱2 衔接

```
onboarding/run (job)
  → jobs: DIAGNOSE → PAIN → PERSONA → COMPETITOR
  → SSE progress → 100% 跳转 /strategy-pack?draft=1
strategy-pack/draft API 聚合各步 JSON 为 StrategyPackDraft
```

### 4.3 舱2 方案包数据模型

```yaml
StrategyPackDraft:
  buyer_personas: [...]
  content_layout_plan: [...]
  competitor_topics: [...]
  differentiation_brief: [...]
  pain_clusters: [...]          # 带 selected 默认
  campaign_directions: [...]
  source_weight_plan: [...]     # D 区；scenario_slots 默认分配自 selected_scenarios
  keyword_library_draft: [...]  # E 区折叠；监测辅助
  freshness: {...}              # 黄条

StrategyPackConfirm:
  selected_persona_ids: []
  selected_scenario_ids: []      # 2～5；决定 content_unit 总数
  differentiation_brief: [...]
  source_weight_plan: [...]     # 可改 weight；scenario_slots 总和=场景数
  confirmed_keywords: [...]
```

确认 → Orchestrator：`GAP_ANALYZE → PLAN → REVIEW → EXECUTE_SKILLS`

**闸门：** 方案包 confirm = **闸门①**（thin KB 未达标则按钮 disabled）；草稿 bulk-approve = **闸门②**。

**布局（FR-UX-15）：** 默认展示 A 画像摘要 + C 场景勾选 + `[确认并生成]`；B 竞品、D 渠道折叠为「展开高级」。

**草稿 Tab（FR-UX-16）：** 三栏 — 预览 | fact_refs 来源 | 机器审告警；通过写入 approval_log。

### 4.4 舱3 效果舱

```
OutcomeDashboard:
  ai_metrics: from monitor_runs (Core)
  hosted_page_stats: PV/form（第一方）
  publish_summary: 各渠道 published/semi/failed + content_asset_id
  conversion_hints: MVP 文案提示；V1.1 consult_logs
  strategy_suggestions: gap_analyze 草案入口（人确认）
```

---

## 5. 知识库中心

### 5.1 实体

Tenant, TargetEngine, Brand, Store, Service, Case, Competitor, **FAQ(Fact)**, RawInput(Signal), Keyword, ExternalCandidate, SourceDiagnosis, Strategy, ContentAsset, PublishTask, MonitorProfile, MonitorRun, HostedPageEvent

### 5.2 主流程（转化闭环 · 后端）

**用户路径：** 开店向导 → 方案包 → 草稿审 → 效果舱 →（迭代）→ 方案包/KB

**系统管道：**

```
录入 KB + onboarding/run（onboarding_graph）
  → competitor 节点内 competitor_graph ReAct
  → strategy_pack/draft → 用户 confirm（闸门①）
  → gap_analyze_graph ReAct → PLAN → EXECUTE（Skill 固定链）
  → 草稿审（闸门②）→ ready → Publish（content_asset_id）→ 效果舱
  → monitor → [临界] StrategyUpdateDraft → 人确认 → 迭代
```

**KB 新鲜度（MVP）：** 任意 KB CRUD 刷新 `kb_updated_at`；方案包 E 区 `GET /kb/freshness`。  
**KB 厚度/gap（V1.1）：** 低分阻断批量生成；content_gaps 优先补 trust 类内容。

---

## 6. 信源诊断（source_diagnose）

```
1. probe_prompt_builder: engines.json + KB 填槽 → 5-10 条/engine
2. EngineAdapter: POST 各 AI 联网 Chat API → citations[]
3. citation_parser → platform_stats, map_gap
4. 存 SourceDiagnosis；高引用问法 → ExternalCandidates / Probe 候选
```

**渠道计划：** 禁止写死行业表；必须引用诊断结果。

---

## 7. FAQs[]（Fact 层，MVP）

```
录入: 表单 Q/A + fact_refs（manual）
升格: RawInputs 整理 → FAQs[]
生成: content_faq 读 FAQs[] → 审核通过 → 回写 FAQs[]（generated）
发布: publish_website 输出 FAQPage Schema
```

---

## 8. 痛点、词库与方案包

### 8.1 beauty_pain_mine / keyword_mine

```
RawInputs + SEO API + diagnose反推
  → exact 去重 → embedding → Faiss(≥0.85) → LLM 簇命名
  → pain_clusters[] + KeywordLibrary draft
```

**词库角色：** 用户确认后 → 监测槽位 + title/summary；**不**作为 content_unit 生产起点。

### 8.2 方案包五区块

| 区块 | 用户输入 | 说明 |
|------|----------|------|
| A 画像 | 确认 persona + layout_plan | |
| B 差异化 | 确认 differentiation_brief | |
| C 场景 | **勾选 scenario** | 最小生产单元 |
| D 渠道 | weight + **承接 scenario 数** | 非「写几篇」 |
| E 展开 | 词库 + freshness 黄条 | |

### 8.3 source_weight_builder

```
source_diagnose.platform_stats
  → weight ∝ cite_share
  → scenario_slots 分配；sum(scenario_slots) = len(selected_scenarios)
  → source_weight_plan[]
```

**Orchestrator PLAN：**

```
total_units = len(selected_scenarios)
topics = campaign(优先) + selected_pains + differentiation
for channel in plan where scenario_slots > 0:
  assign content_units；each: 1 scenario + 1 skill + 1 channel
```

---

## 9. content_unit 与内容工厂

```yaml
content_unit:
  core_intent, scenario, channel, topic_angle, target_persona
  fact_refs[]
  output: { skill, publish_mode }
```

**生成链 MVP：** `kb_fetch(fact_refs) → Layer Prompt → Skill → 机器审 → draft`  
**V1.1：** 可选 hybrid_retrieve enrich Layer3，仍须 fact_verify。

---

## 10. 发布中心

```
PublishAdapter:
  HostedPageAdapter    AUTO
  WordPressAdapter     AUTO optional
  XhsAdapter           AUTO, on_fail→ExportAdapter
  ZhihuAdapter         AUTO, on_fail→ExportAdapter
  GuidedAdapter        点评/美团
```

发布任务：`draft → ready → publishing → published | failed(SEMI)`；**必写 content_asset_id**。

---

## 11. 监测中心

### 11.1 MonitorProfile

```yaml
target_engines: [doubao, deepseek]
core_prompts: MVP=KeywordLibrary.confirmed + selected_scenarios；V1.1=scenario 为主
probe_prompts: agent_generated               # ≤10/engine
thresholds:
  mention_rate_min: 0.30
  consecutive_weeks: 2
  source_exposure_zero_weeks: 2
```

### 11.2 执行与迭代

```
weekly: monitor_run(core) + monitor_run(probe)
post_publish: monitor_run(core subset, +24h)

if threshold_breach → gap_analyze → StrategyUpdateDraft → 效果舱 [确认]
```

---

## 12. 数据表（逻辑）

tenants(**kb_updated_at**), brands, stores, services, raw_inputs, keywords, faqs, target_engines, source_diagnoses, strategies(...), strategy_pack_drafts, content_assets(fact_refs, review_result, **approval_log**), publish_tasks(**content_asset_id**), hosted_page_events, monitor_profiles, monitor_runs, jobs, faiss_indexes, agent_traces

---

## 13. API 概要

| 方法 | 路径 | 说明 |
|------|------|------|
| CRUD | /api/tenants/{id}/kb/* | 知识库 |
| GET | /api/tenants/{id}/kb/freshness | KB 新鲜度 |
| POST | /api/tenants/{id}/onboarding/run | 舱1 |
| GET | /api/tenants/{id}/onboarding/status | 进度 SSE |
| GET | /api/tenants/{id}/strategy-pack/draft | 舱2 草案 |
| POST | /api/tenants/{id}/strategy-pack/confirm | 闸门① |
| GET | /api/tenants/{id}/content-drafts | 草稿+machine_review |
| POST | /api/tenants/{id}/content-drafts/bulk-approve | 闸门② |
| GET | /api/tenants/{id}/outcomes | 舱3 |
| POST | /api/publish-tasks | 发布 |
| GET | /api/monitor/runs | 监测 |

---

## 14. 安全与异步

JWT+RBAC+tenant 隔离；Skill 禁跨 tenant；爬虫白名单。Redis 队列 + jobs 状态机。

---

## 15. 延后能力

**V1.1：** trust_asset、scenario-first Core、KB thickness/gap、ConsultLog、hybrid_retrieve。  
**V2：** adapt_engine、B2B 包、完整转化 Dashboard、V2a 偏好。  
**V2+：** V2b rerank · V2c 可选蒸馏。

---

*概要设计 v4.1*
