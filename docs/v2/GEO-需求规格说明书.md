# GEO 智能品牌平台 — 需求规格说明书 v2

> **版本**：V2.5 | **日期**：2026-07-04 | **关联**：PRD-v3.md · 架构 §2.1

---

## 0. 第一性原理（项目锚点）

> 面向**特定目标人群**，匹配**真实问答场景**，输出**信息增量**与**差异化价值**，建立**品牌专业信任**，完成**咨询与成交转化**。

- **价值公式：** 内容价值 ≈ 信息增量 × 品牌信任度；发文数量为次要变量  
- **North Star：** AI 信任资产工厂 → 分渠道可见度 → 转化闭环（非软文铺量工厂）  
- **MVP：** 生美垂直验证底座；**V1.1/V2** 见 §12 二期需求  

---

## 1. 引言

### 1.1 目标

多企业 GEO SaaS，MVP 生美。3 步：录库 → 确认策略与内容 → 发布与监测。

### 1.2 边界

不做：保证排名第一、刷好评、虚构品牌、完整 CMS、Neo4j 知识图谱、MVP 全网负面监测。

### 1.3 外部共识（16问/新榜/navyum）

DSS；先测信源；跨平台常不兼容；AI 应答展现；禁关键词堆砌；禁虚构品牌。

---

## 2. 角色与约束

| 角色 | 诉求 |
|------|------|
| Owner/Admin | 建库、确认策略、发布 |
| Editor | 改内容、提交审核 |
| Viewer | 看报告 |

**技术约束：** Vue3+TS + FastAPI + **Pydantic v2 全量校验** + Celery + LangSmith trace；**L1 jobs + L2 LangGraph + L3 ReAct Harness**；详《架构设计》§2.3～§2.4。

---

## 2d. 可观测与 MCP（MVP）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| OBS-01 | **LangSmith** 接入 LangGraph/LLM Gateway | P0 |
| OBS-02 | trace metadata：tenant_id, job_id, graph_name（无 PII 正文） | P0 |
| OBS-03 | prod LangSmith **采样**（如 10%） | P0 |
| OBS-04 | **agent_traces** 与 LangSmith 双写（产品审计保留） | P0 |
| OBS-05 | LangSmith Dataset + CI eval（competitor/gap fixture） | P1 |
| MCP-01 | **geo-mcp-server** 只读：kb_fetch, diagnose_stats, engine_probe | P1 |
| MCP-02 | MCP 与 Harness **ToolRegistry 同一实现** | P1 |
| MCP-03 | MCP 禁止 write_fact / publish | P0 |

---

## 2e. API / Skill Pydantic 校验（MVP P0 · 必须）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| VAL-01 | 所有 Router 使用 Pydantic Request/Response Model | P0 |
| VAL-02 | `StrategyPackDraft/Confirm` 等三舱 schema 独立文件 | P0 |
| VAL-03 | 每个 Skill 定义 input/output Pydantic Model | P0 |
| VAL-04 | LLM JSON 输出 `model_validate`；失败重试 1 次 | P0 |
| VAL-05 | 策略类 Model `extra="forbid"` | P0 |
| VAL-06 | OpenAPI 导出供前端类型生成 | P1 |

---

## 2b. 三舱 UX 需求（MVP P0）

> PRD §2。操作链路 **7 步压 3 步**；用户闸门 **2 次**（方案包 + 草稿审）。

### 2b.1 舱1 · 开店向导 Onboarding Wizard

| 编号 | 需求 | 优先级 |
|------|------|--------|
| UX-01 | 6 步表单向导：AI/店信息/目标客户/竞品/核心优势/RawInputs | P0 |
| UX-02 | `POST onboarding/run` 触发异步 job 链（诊断→痛点→画像→竞品） | P0 |
| UX-03 | 进度 SSE/轮询；完成后跳转方案包 | P0 |

### 2b.2 舱2 · 方案包 Strategy Pack

| 编号 | 需求 | 优先级 |
|------|------|--------|
| UX-04 | 单页 A～E 五区块（画像/差异/场景/渠道/展开） | P0 |
| UX-05 | `GET strategy-pack/draft` 聚合后端草案 | P0 |
| UX-06 | `[确认并生成草稿]` → `POST confirm` → PLAN+EXECUTE 一次触发 | P0 |
| UX-07 | 同页草稿列表 + machine_review + 单条/批量通过 | P0 |
| UX-08 | D 区篇数 **默认=len(已选场景)**，≤5 | P0 |
| UX-09 | 原策略方向页/信源权重页 **不单独路由**（逻辑保留 API） | P0 |

### 2b.3 舱3 · 效果舱 Outcome Dashboard

| 编号 | 需求 | 优先级 |
|------|------|--------|
| UX-10 | `GET outcomes` 聚合：AI KPI + 发布状态 + 托管页 PV/表单 | P0 |
| UX-11 | 一键发布入口（ready assets） | P0 |
| UX-12 | ConsultLog 录入 + 简化归因 | V1.1 |
| UX-13 | 临界/策略建议入口 | P0 |

---

## 2c. Agent 运行时（MVP P0）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| AG-01 | **LangGraph** `onboarding_graph` 线性子图 | P0 |
| AG-02 | **competitor_graph** + ReAct（engine_probe→page_fetch→draft） | P0 |
| AG-03 | **gap_analyze_graph** + ReAct（kb_thickness→gaps） | P0 |
| AG-04 | **ReActHarness**：ToolRegistry、max_steps、tenant 隔离 | P0 |
| AG-05 | **agent_traces** 审计落库 | P0 |
| AG-06 | 禁止 write_fact / auto_confirm / publish 工具 | P0 |
| AG-07 | 正文 Skill **无 ReAct**（固定 kb_fetch 链） | P0 |
| AG-08 | Eval harness：beauty fixture CI 回归 competitor/gap 图 | P1 |

---

## 3. 知识库（M2）

### 3.1 原则

- KB = **对外发布事实的唯一权威**
- 多源分析，**写入 Fact 须确认**
- Fact 带 `updated_at`；gap 检测；fact_verify 失败拒发
- 租户级 **`kb_updated_at`**（任意 KB 子表变更时刷新）
- 生成策略前 **`GET /kb/freshness`**；客户端展示最近改动时间与诊断/策略对比提示
- **正文事实主链：** `kb_fetch(fact_refs)` 按 ID 拉 Fact（可审计）；V1.1 可选 `hybrid_retrieve` 仅补表述，不替代主链（见 §5.0）

### 3.2 结构

```
Enterprise
├── TargetEngines[]
├── Brand / Stores[] / Services[] / Cases[] / Competitors[]
├── FAQs[]              # Fact
├── RawInputs[]         # Signal
├── KeywordLibrary[]
├── ExternalCandidates[]
└── (meta) kb_updated_at, kb_revision
# campaign_directions / differentiation_brief：策略方向页提交，写入 Strategy 草案
```

### 3.3 录入（MVP）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M2-01 | 表单：品牌/门店/项目 | P0 |
| M2-02 | RawInputs 粘贴（客服/评价/FAQ） | P0 |
| M2-03 | TargetEngines 主攻/次攻 | P0 |
| M2-04 | KeywordLibrary Agent 出词→用户确认 | P0 |
| M2-08 | **FAQs[] CRUD**（Q/A/fact_refs；手工+从 Raw 升格） | P0 |
| M2-09 | content_faq 生成后 **回写 FAQs[]**（用户确认） | P0 |
| M2-05 | SeedKeywords | P1 |
| M2-06 | 文件上传 MinIO/OSS | P1 |
| M2-07 | 链接录入/店名补全 | V1.1 |
| M2-10 | **kb_updated_at** 任意 Fact/Signal/FAQ 变更自动刷新 | P0 |
| M2-11 | **GET /kb/freshness** 供策略页展示 | P0 |
| M2-12 | **SEO/问答 API** 接入（→ External，确认后进词库） | P0 |

---

## 4. 信源诊断、痛点、策略（M3）

### 4.1 信源诊断（source_diagnose）

#### 4.1.1 探测 Prompt 生成

| 输入 | 处理 |
|------|------|
| TargetEngines | 决定对哪些 AI 测 |
| Stores.city, Brand.name | 填 `{city}` `{brand}` |
| Services[].name | 填 `{project}` |
| engines.json 模板 | local/intent/brand/compare |
| LLM 扩写（可选） | +3 变体/店 |

输出：`diagnose_prompts[engine][]`，每 engine 5～10 条。

#### 4.1.2 怎么测（API，非自建爬虫）

```
EngineAdapter.call(engine, prompt):
  1. 选 adapter：DoubaoAdapter | DeepSeekAdapter | KimiAdapter | WenxinAdapter
  2. HTTP POST 厂商 Chat Completions API
     - enable_search / plugins / bot_id（按厂商文档开联网）
  3. 响应解析：
     - answer_text
     - citations[] 或 search_results[] → normalize_url → cited_urls
  4. 聚合 platform_stats（域名→小红书/点评/知乎/媒体/地图）
  5. map_gap：本地类 prompt 无地图/POI 来源 → true
```

| 项 | 说明 |
|----|------|
| 密钥 | 平台 `.env` 注入；按 tenant 配额计费 |
| 频率 | 诊断批次异步；每 prompt 间隔限速 |
| 存储 | `source_diagnoses` JSONB per engine |

高引用问法 → ExternalCandidates；可选进 Probe 池 / KeywordLibrary 提案。

#### 4.1.3 FAQs[] 与 Signal 分工

| | RawInputs(faq) Signal | FAQs[] Fact |
|--|----------------------|-------------|
| 形态 | 粘贴、非结构化 | Q/A 字段、fact_refs |
| 用途 | 挖痛点 | 发布、content_faq 主数据 |
| 升格 | 人工整理 → FAQs[] | — |
| 回写 | — | content_faq 审核通过 → source=generated |

### 4.2 痛点、词库与策略方向页

| 优先级 | 来源 | MVP |
|--------|------|-----|
| P0 | RawInputs | ✅ |
| P0 | **SEO/问答 API** | ✅ |
| P0+ | source_diagnose 反推 | ✅ |
| P1 | 手动补充 | ✅ |
| P3 | 定向爬虫 | V1.2 |

**聚类（beauty_pain_mine / keyword_mine 共用）：**

1. exact 去重  
2. embedding 向量  
3. **Faiss** 相似合并（threshold≥0.85，per-tenant index）  
4. LLM **兜底**：簇 theme 命名、无法归类句、scenario 文案  

**策略方向页（M3-UI，Orchestrator 前）：**

| 区块 | 字段 | 说明 |
|------|------|------|
| **画像** | buyer_personas[], content_layout_plan[] | persona_analyze 输出，用户确认 |
| 痛点 | selected_pain_cluster_ids[] | beauty_pain_mine，用户勾选 |
| 爆点 | campaign_directions[] | 用户填 1～2 个主推方向 |
| 差异化 | differentiation_brief[] | competitor_content_analyze 草案，用户确认/编辑 angle |
| 词库 | KeywordLibrary confirmed | keyword_mine 草案，用户删改确认 |

**信源权重页（M3-UI，Orchestrator 前，在策略方向页之后）：**

| 列 | 字段 | 说明 |
|----|------|------|
| 诊断结果 | cite_share, top_domains | 来自 source_diagnose（只读） |
| 权重 | weight | 用户调整，归一化 |
| 篇数 | article_count | 该渠道本轮生成几篇 |
| 渠道 | channel, publish_mode, default_skill | 系统映射，可改 |

提交 → `source_weight_plan[]`。

**Orchestrator：** 按 `article_count` 从选题池分配 content_unit，每篇绑定单渠道单 Skill。

**KB 新鲜度：** 进入策略方向页 / 点击「生成策略」时调用 freshness API，展示 `kb_updated_at` 及相对上次诊断/策略是否过期（见 §3.1）。

**beauty_pain_mine 输出：** `{theme, frequency, sample_quotes[], suggested_persona}`

**keyword_mine 输出：** KeywordLibrary draft → 确认 → Core 池

### 4.2a 用户画像 persona_analyze（MVP P0）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M3-10 | **persona_analyze** Skill：行业+KB+RawInputs→buyer_personas[] | P0 |
| M3-11 | 输出 **content_layout_plan[]**（人群→内容类型→渠道→转化路径） | P0 |
| M3-12 | 策略方向页 **画像区块**：确认 primary persona + 布局方案 | P0 |

**buyer_personas 字段：** `role_label, pain_tags[], decision_stage, concerns[], trust_triggers[]`  
**content_layout_plan 字段：** `persona_id, content_types[], recommended_channels[], conversion_path, sample_scenarios[]`

生美 MVP 角色模板见行业包 `personas.json`；B2B 采购链字段 V2 扩展。

### 4.2b 竞品内容分析 competitor_content_analyze（MVP P0）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M3-13 | **competitor_content_analyze**：AI 对比探测（EngineAdapter + compare 模板） | P0 |
| M3-14 | 可选 **competitor_page_fetch**（点评/小红书白名单 URL 轻量提取） | P0 |
| M3-15 | 输出 competitor_topics[] + differentiation_brief[] 草案 + content_gaps[] | P0 |
| M3-16 | 策略方向页 **差异化区块**：确认/编辑 angle，非纯手工从零填写 | P0 |

**MVP 不做：** 任意域名全网爬虫、竞品账号全平台监控（→ V2）。

**延后 V1.1+：** trust_asset 产线、全网负面、hybrid_retrieve 全文检索 enrich

### 4.3 content_unit（策略输出）

```yaml
content_unit:
  core_intent: pain | campaign | differentiation
  scenario: "敏感肌能不能做皮肤管理"
  channel: xiaohongshu              # 来自 source_weight_plan 分配的篇位
  topic_angle: "专业科普"
  target_persona: "hesitant_new"
  variants: [...]
  fact_refs: [...]
  output: { skill: beauty_xhs_note, publish_mode: SEMI }  # 每单元 1 渠道 1 Skill
```

**Strategy 还含：** `buyer_personas[]`, `content_layout_plan[]`, `competitor_topics[]`, `engine_plan[]`, `source_weight_plan[]`, `monitor_plan`, `content_gaps[]`.

用户确认策略后 Skill 按 content_unit **逐篇**执行。

### 4.4 Review Agent（策略阶段）

- 合规：广告法、生美禁词
- 事实：content_unit 是否有 KB 依据
- 虚构品牌拦截

---

## 5. 内容工厂（M5）与审核

### 5.0 KB 取数（kb_fetch 与混合检索）

**MVP 主链 — `kb_fetch(fact_refs)`：**

| 项 | 说明 |
|----|------|
| 输入 | Orchestrator 写入的 `fact_refs[]`（如 `service:03`, `faq:12`） |
| 行为 | 按 ID 读取 Fact 层 **完整记录**（Brand/Stores/Services/Cases/Competitors/FAQs） |
| 输出 | Layer3 Prompt 用的 KB 快照 JSON |
| 为何不用向量搜 | 发布事实须 **可追溯、可 fact_verify**；ID 主链确定性最强 |

**不全怎么办：** 一篇挂多条 fact_refs；Orchestrator 按 scenario 绑定；策略阶段 Review 检 KB 依据。

**过时怎么办：** `kb_updated_at` + freshness API；KB 晚于上次策略则黄条提示（建议更新 KB 或重跑诊断），不静默用旧数据。

**V1.1 增强 — `hybrid_retrieve`（Faiss 语义 + KeywordLibrary BM25）：**

| 检索源（均在 KB 内） | 用途 | 能否直接当发布事实 |
|---------------------|------|:------------------:|
| RawInputs（客服/评价片段） | Layer3 补充 **真实用户表述**；variants 扩展 | ❌ 须引述且不引入新数值 |
| FAQs[] / Services / Cases | fact_refs **候选推荐**；相关上下文 | ✅ 升格为 fact_refs 后可 |
| KeywordLibrary.confirmed | keyword_slots / monitor_phrase 匹配 | ✅ 已确认词 |
| diagnose 高引用问法 | Probe / variants | ❌ 进 External，确认后入词库 |

**不做：** 检索 Prompt 模板；检索替代 keyword_mine；Agentic 多跳 RAG 进默认生成路径。

**关键词分工：** keyword_mine 发现草案 → 用户确认 → 生成时 LLM 只填 **已确认词** 进槽位，不现场发明监测词。

### 5.1 生成约束

- 基于 Fact + fact_refs；首段结论 + 文末总结
- 关键词仅 title/summary/faq_q；禁堆砌
- DSS：Depth / Support / Source

### 5.2 机器审核清单（P0）

| # | 检查项 | Skill/规则 | 不通过 |
|---|--------|-----------|--------|
| A1 | 价格/区间匹配 Services | fact_verify | 拒发/标风险 |
| A2 | NAP 匹配 Stores | fact_verify | 拒发 |
| A3 | 项目描述/禁忌有依据 | fact_verify | 拒发 |
| A4 | 案例可追溯到 Cases | fact_verify | 拒发 |
| A5 | 竞品仅 KB 内实体 | fact_verify | 拒发 |
| A6 | fact_refs 非空且有效 | fact_verify | 拒发 |
| A6b | FAQ 答案与 FAQs[]/Services 一致 | fact_verify | 拒发 |
| A7 | 广告法禁词（最好/第一/100%） | compliance_check | 拒发 |
| A8 | 生美禁词/医美疗效表述 | beauty_compliance | 拒发 |
| A9 | 关键词正文堆砌 | 规则 | 警告/拒发 |
| A10 | 清单/横评无虚构品牌 | Review | 拒发 |
| A11 | AI 生成标识（法规） | compliance_check | 必含 |

### 5.3 机器审核（P1）

| # | 检查项 | Skill |
|---|--------|-------|
| B1 | DSS 三维评分 | dss_score |
| B2 | 渠道体例（FAQ Schema/小红书结构） | output_schema |

### 5.4 人工审核（P0）

内容工作台：预览 | 对照 fact_refs | 处理机器告警 | 修改 | **通过→ready** | 打回

**状态：** draft → ready → published（发布中心）

---

## 6. 发布（M6）

| 模式 | 渠道 | MVP |
|------|------|-----|
| AUTO | 托管页、WordPress | ✅ |
| AUTO→SEMI | 小红书、知乎（OAuth/加密账密；失败导出） | ✅ |
| GUIDED | 点评/美团 | ✅ |

M6-05：发布后 24h Core 子集复测；M6-04：Schema + llms.txt

---

## 7. 监测（M7）

### 7.1 双 Prompt 池

| 池 | 来源 | 用途 | 临界触发 |
|----|------|------|:--------:|
| **Core** | KeywordLibrary confirmed intent/local | 主 KPI、周报 | ✅ |
| **Probe** | Agent+diagnose 模板，≤10/engine/周 | 探索、扩词提案 | ❌ |

### 7.2 指标

| 指标 | 说明 |
|------|------|
| 品牌提及率 | Core：含品牌回答数/ Core 总数 |
| 信源列表露出率 | Core：含自有 URL 的回答比例 |
| AI 应答展现 | 品牌出现次数 |
| 引用来源数 | citation 条数 |
| 推荐顺位/SoV/情感 | 存储，V1.1 作触发 |

### 7.3 迭代触发（Orchestrator 草案）

- Core 提及率连续 **2 周 <30%**（主攻 engine，可调）
- Core 信源露出 **2 周 =0%**
- Core 提及率 **2 周连降 >20%**

→ gap_analyze → 策略更新草案 → **用户确认**

---

## 8. 行业包（M9）

`beauty_local`：Schema、Prompt、Skill 清单、禁词、engines 模板、persona 模板（3 个）。**产品预置，非 Agent 生成。**

MVP 不做 Neo4j；V1.1 可选 entity_relations。

---

## 9. Skill 清单（MVP）

**平台：** kb_ingest, entity_extract, fact_verify, compliance_check, content_faq, publish_website, publish_export, monitor_setup, monitor_run, report_generate

**beauty_local：** source_diagnose, source_weight_builder, **persona_analyze**, **competitor_content_analyze**, keyword_mine, beauty_pain_mine, beauty_gap_diagnose, dss_score, beauty_xhs_note, beauty_zhihu_answer, beauty_merchant_copy, beauty_compliance, nap_consistency_check

---

## 10. 验收（AC）

| # | 标准 |
|---|------|
| AC-01 | 全流程 1 店跑通 |
| AC-02 | fact_refs 可追溯 |
| AC-03 | 禁词拦截 |
| AC-04 | Core 监测 ≥2 engine |
| AC-05 | 租户隔离 |
| AC-06 | 未确认不发布 |
| AC-07 | 小红书失败可 SEMI |
| AC-08 | FAQs[] 录入 + content_faq 回写 |
| AC-09 | 策略方向页 + KB 新鲜度展示 |
| AC-10 | 信源权重页 + 按篇数生成 content_unit |
| AC-11 | Faiss 聚类 + SEO API |
| AC-12 | persona_analyze + content_layout_plan 确认 |
| AC-13 | competitor_content_analyze + 差异化草案确认 |
| AC-14 | 三舱：开店向导 → 方案包一次确认 → 草稿审 |
| AC-15 | LangGraph 三子图 + ReActHarness + agent_traces |
| AC-16 | LangSmith trace + Pydantic 全接口校验 |
| AC-17 | geo-mcp-server 只读工具（P1 可延后验收） |

---

## 12c. Agent ToB 与偏好学习（摘要）

| 主题 | 文档 | 要点 |
|------|------|------|
| Agent ToB 三层 | PRD §7.1 · 架构 §2.1.0 | L3 垂域=壁垒；Skill 喂厚行业包 |
| 偏好/蒸馏 V2+ | PRD §11.8 · 架构 §13b.5 | V2a→V2b→V2c；人确认；不学 Fact |

---

## 12. 二期需求（V1.1 / V2 · MVP 后 · 概要）

> persona/competitor 已在 **MVP**；本节为 V1.1/V2 其余能力。详见 PRD §11。

### 12.1 V1.1（生美可用 + 通用底座）

| 编号 | 需求 | 说明 |
|------|------|------|
| V11-01 | **trust_asset 产线** | case_builder / faq_from_raw → Fact |
| V11-02 | **hybrid_retrieve** | Faiss+BM25 enrich Layer3 |
| V11-03 | **scenario-first Core 池** | Core prompts 主来源=pain scenario |
| V11-04 | **KB 厚度 + gap 评分** | 低厚度提示补 trust |
| V11-05 | **信源权重 scenario 承接** | 篇数=scenario 数上限 |
| V11-06 | **ConsultLog + 简化归因** | 高提及零咨询→策略草案 |
| V11-07 | hybrid_retrieve 受限 ReAct（max 3 步，只读） | V1.1 |

### 12.2 V2 二期（B2B / 制造业包）

| 编号 | 需求 | 说明 |
|------|------|------|
| V2-01 | 深度专业内容 Skill | 技术对比、选型指南、方案解析、白皮书 |
| V2-02 | fact_verify 政策/参数 | 行业参数库、政策规则 |
| V2-03 | **adapt_engine 一源多态** | core_material→长文/视频脚本/短文案/商务卖点 |
| V2-04 | 竞品**大规模**定向采集 | 官网/行业媒体；扩大白名单（MVP 已有 AI 探测+轻量抓取） |
| V2-05 | 转化报表 Dashboard | 流量+咨询+转化漏斗；CRM/Webhook |
| V2-06 | 渠道数据 API | 小红书等只读统计（可行则 AUTO，否则 SEMI） |
| V2-07 | 全网负面监测与对冲 | 延后同 PRD |
| V2-09 | **偏好学习 V2a** | feedback→preference_profile→PLAN 排序 |
| V2-10 | 检索 rerank V2b | 本租户 preference_examples |
| V2-11 | 可选蒸馏 V2c | 语气/体例 opt-in；禁事实蒸馏 |

---

## 11. 计费

内容按条；监测包月（Core prompt 配额分档）。钱包与订阅分离。

---

*需求规格 v2.5*
