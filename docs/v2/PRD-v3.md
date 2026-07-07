# GEO 多企业 AI 可见度运营平台 — PRD v3.1

> **状态**：讨论定稿基线 | **日期**：2026-07-04  
> **MVP 行业**：生美 `beauty_local`  
> **详版**：`v2/GEO-需求规格说明书.md` · `GEO-架构设计说明书.md` · `GEO-概要设计说明书.md`

---

## 0. 第一性原理（项目锚点）

> 面向**特定目标人群**，匹配**真实问答场景**，输出**信息增量**与**差异化价值**，建立**品牌专业信任**，完成**咨询与成交转化**。

| ❌ 禁止 | ✅ 方向 |
|--------|--------|
| 批量伪原创 | KB + fact_verify |
| 追求发文数量 | scenario 驱动，篇数=结果非目标 |
| 一稿通发 | 分渠道 Skill（V2 一源多态） |
| 只盯 AI 提及 | 可见度 + 信任 + 转化 |
| 关键词堆砌 | scenario-first |

**价值公式：** 内容价值 ≈ 信息增量 × 品牌信任度  
**North Star：** AI 信任资产 → 分渠道可见度 → 转化（非软文工厂）

---

## 1. 产品定义

AI 时代选购参考转向豆包/DeepSeek/Kimi/文心。**GEO = 让 AI 能引用、能采信你的真实品牌信息。**

| 维度 | 说明 |
|------|------|
| 产品 | 多企业 GEO SaaS |
| 差异化 | KB 零幻觉 · 先选 AI 再测信源 · scenario 分渠道 · Core/Probe 监测 |
| 不是什么 | 软文工厂、保证第一、虚构品牌、刷好评、铺量 KPI |

---

## 2. 用户旅程：三舱 · 对外 3 步

> 复杂分析封装在系统内；用户 **2 次确认闸门**（方案包 + 草稿审）。

### 2.1 三舱对照

| 舱 | 用户说 | 系统后台 |
|----|--------|----------|
| **舱1 懂我** | 告诉我店的信息 | 建库 → 诊断 → 痛点/词库 → 画像 → 竞品 |
| **舱2 定方案** | 看方案、确认出稿 | PLAN → EXECUTE → 机器审 → **草稿审** |
| **舱3 出结果** | 发布、看效果 | 发布 → 监测 → 效果舱 |

### 2.2 对外 3 步

**Step 1 · 开店向导** — 一次提交：选 AI、店信息、目标客户、竞品、核心优势、RawInputs → `[开始分析]` → 后台 job 链（进度条）。

**Step 2 · 方案包 + 草稿审**

1. **方案包**（一页，见 §2.3）→ `[确认并生成草稿]`
2. **草稿列表** → 逐条或批量 `[通过]`

**Step 3 · 效果舱** — 发布（AUTO→失败 SEMI）+ Dashboard（AI KPI + 托管页流量；V1.1 +咨询）。

**铁律：** 无 Fact 不发布；篇数默认 = 已选 scenario 数（≤3～5）。

### 2.3 方案包 Strategy Pack（合并原策略方向页 + 信源权重页）

| 区块 | 来源 | 用户操作 |
|------|------|----------|
| **A 画像** | persona_analyze | 确认 persona + content_layout_plan |
| **B 竞品** | competitor_content_analyze | 确认/编辑 differentiation_brief |
| **C 场景** | pain + campaign + 差异化 | 勾选 3～5 个 scenario |
| **D 渠道** | source_weight_builder | 调 weight；篇数默认=C 区场景数 |
| **E 展开** | keyword_mine、freshness | 词库、KB 黄条（折叠） |

**API：** `GET strategy-pack/draft` · `POST strategy-pack/confirm` · `GET content-drafts` · `POST content-drafts/bulk-approve`

### 2.4 开店向导字段

| 步 | 字段 | 写入 |
|----|------|------|
| 1 | TargetEngines | target_engines |
| 2 | 品牌/门店/项目 | KB Fact |
| 3 | 目标客户（模板多选） | persona 种子 |
| 4 | 竞品 + 可选链接 | competitors[] |
| 5 | 一句话核心优势 | brand.differentiator |
| 6 | RawInputs | Signal |

提交 → `POST onboarding/run` → `DIAGNOSE → PAIN → PERSONA → COMPETITOR` → 跳转方案包。

### 2.5 效果舱指标

| 指标 | MVP | V1.1 |
|------|-----|------|
| AI 提及 / 信源露出 | Core | ✅ |
| 托管页 PV / 表单 | ✅ | ✅ |
| 咨询 / 归因 | — | ConsultLog |
| 策略建议 | 临界→草案 | + 高提及零咨询 |

---

## 3. 已定决策（速查）

| 议题 | 决策 |
|------|------|
| KB | Fact/Signal/External；FAQs[]；`kb_updated_at` + freshness |
| 三舱 UX | 开店向导 + 方案包 + 效果舱（无独立策略/权重路由 MVP） |
| 画像 / 竞品 | **MVP P0**；输出进方案包 A/B 区 |
| 痛点 / 词库 | RawInputs + SEO API + Faiss 聚类 + diagnose 反推 |
| content_unit | scenario + persona + topic_angle；**每篇 1 渠道 1 Skill** |
| 正文取数 | MVP `kb_fetch(fact_refs)`；V1.1 hybrid_retrieve enrich |
| 监测 | Core + Probe（≤10/engine/周）；临界仅 Core |
| 发布 | 托管页 AUTO；小红书/知乎 AUTO 失败 → SEMI |
| Agent | L1 jobs + L2 LangGraph 子图 + L3 ReAct；正文 Skill **无 ReAct** |
| 延后 | trust_asset(V1.1)、adapt_engine/B2B(V2)、偏好蒸馏(V2+) |

---

## 4. 知识库

```
Enterprise
├── TargetEngines[] · Brand · Stores[] · Services[] · Cases[] · Competitors[]
├── FAQs[]（Fact）· RawInputs[]（Signal）· KeywordLibrary[] · ExternalCandidates[]
└── kb_updated_at（租户级）
```

| 层 | 用途 | 可发布 |
|----|------|:------:|
| Fact | NAP/项目/案例/FAQ | ✅ |
| Signal | 痛点线索 | ❌ |
| External | 外部采集 | 确认后入 Fact |

---

## 5. 核心能力（MVP）

### 5.1 系统管道（后端）

```
onboarding/run
  → source_diagnose → pain/keyword_mine → persona_analyze → competitor_content_analyze
  → strategy_pack/draft → 用户 confirm
  → GAP_ANALYZE → PLAN → EXECUTE_SKILLS → 机器审
  → 草稿审 → PUBLISH → monitor → 效果舱
```

### 5.2 信源诊断 source_diagnose

- **Prompt：** `engines.json` 模板 + KB 填槽 → 5～10 条/engine（local/intent/brand/compare）
- **探测：** EngineAdapter 联网 Chat API → 解析 citations → `platform_stats`
- **原则：** 调 AI 联网引用，**非自建爬虫**；密钥平台侧
- **输出：** 平台分布、map_gap、高引用问法 → External/Probe 候选

### 5.3 用户画像 persona_analyze（MVP）

**输入：** 行业包 + KB + RawInputs + 用户角色模板  
**输出：**

- `buyer_personas[]`：role、pain_tags、decision_stage、trust_triggers
- `content_layout_plan[]`：人群 → 内容类型 → 渠道 → **转化路径**

生美示例：敏感肌新客（FAQ+案例→托管页/小红书）；比价党（差异化→知乎/托管页）。  
B2B 采购链矩阵 → **V2**。

### 5.4 竞品分析 competitor_content_analyze（MVP）

| 通道 | 做法 |
|------|------|
| **A AI 对比探测** | compare 模板 × 竞品名 → EngineAdapter → 热门话题、citation 形态 |
| **B 公开页轻抓** | 用户提交点评/小红书 URL（白名单）→ 摘要进 External |

**输出：** `competitor_topics[]`、`differentiation_brief[]` 草案、`content_gaps[]`  
**不做：** 全网爬虫、竞品全平台监控（→ V2）。

### 5.5 痛点与词库

```
RawInputs + SEO API + diagnose反推
  → exact 去重 → embedding → Faiss(≥0.85) → LLM 簇命名
  → pain_clusters[] + KeywordLibrary 草案 → 用户确认
```

词库辅助监测槽位；**生产单元是 scenario**，不是关键词。

### 5.6 渠道分配与 content_unit

**source_weight_builder（方案包 D 区）：** diagnose `cite_share` → 渠道 weight；**篇数 = 已选 scenario 数**。

**Orchestrator PLAN：**

```
选题池 = campaign(优先) + pain + differentiation
按渠道 weight 分配 content_unit：每篇 = 1 scenario + 1 渠道 + 1 Skill
```

```yaml
content_unit:
  core_intent: pain | campaign | differentiation
  scenario, channel, topic_angle, target_persona
  fact_refs[], output: { skill, publish_mode }
```

### 5.7 内容生成与 KB 取数

**MVP 主链：** `fact_refs → kb_fetch(按ID拉Fact) → Layer1/2/3 Prompt → LLM → fact_verify`

| 担心 | 对策 |
|------|------|
| 不全 | 多绑 fact_refs；Review 检 KB 依据 |
| 过时 | kb_updated_at + freshness 黄条 |
| 乱编 | fact_verify 失败拒发 |

**V1.1：** kb_fetch 后 optional `hybrid_retrieve`（Faiss+BM25）仅 enrich 表述，**不替代 fact_refs**。  
**Faiss MVP：** 仅痛点/词库聚类，非正文 RAG。

详版：架构 §6a、需求规格 §5.0。

### 5.8 审核 · 发布 · 监测

| 环节 | MVP |
|------|-----|
| **机器审** | fact_verify、compliance、beauty_compliance、禁堆砌、禁虚构品牌 |
| **人工审** | 草稿工作台 → `ready` |
| **发布** | 托管页 AUTO；小红书/知乎 AUTO→SEMI；点评 GUIDED |
| **监测** | Core（~20/engine）+ Probe（≤10/engine）；提及率、信源露出 |
| **迭代** | Core 2 周临界 → 策略更新**草案**（人确认） |

审核清单：需求规格 §5。

---

## 6. 模块一览

| 模块 | MVP |
|------|-----|
| M1 租户/RBAC | ✅ |
| M2 知识库 | ✅ |
| M3 诊断+策略+Agent | ✅ persona/竞品/方案包 |
| M3-UI 三舱 | ✅ onboarding / strategy-pack / outcomes |
| M5 内容+审核 | ✅ |
| M6 发布 | ✅ |
| M7 监测 Core+Probe | ✅ |
| M8 报告/效果舱 | ✅ |
| M9 beauty_local 行业包 | ✅ |

---

## 7. 技术选型与 Agent ToB

| 层 | 选型 |
|----|------|
| 前端 | Vue3 + Vite + TS + Element Plus + Pinia |
| 后端 | Python 3.11+ · FastAPI · **Pydantic v2 全量校验** |
| 数据 | PostgreSQL · Redis/Celery · Faiss · OSS |
| LLM | `packages/llm/gateway` + 4 EngineAdapter |
| Agent | **L1** jobs+Celery · **L2** LangGraph 子图 · **L3** ReAct Harness |
| 可观测 | Sentry · LangSmith · agent_traces |
| 部署 | Docker Compose → ECS + RDS |

### 7.1 Agent ToB 三层（K博对标）

| 层 | GEO | 状态 |
|----|-----|------|
| L1 通用 LLM | LLM Gateway | 设计 ✅ |
| L2 Harness | jobs + LangGraph + ReAct | MVP 设计 ✅ |
| **L3 垂域** | 行业包 + Skill + KB + 三舱 | **壁垒 · 重心** |

| 热词 | 做法 |
|------|------|
| Skill | 感知/策略/生产/治理 → 喂厚 L3 |
| Agentic RAG | 仅 competitor/gap 子图 ReAct |
| 蒸馏/自进化 | V2+ §9.3；学偏好不学 Fact |

**正文 Skill：** 固定链 kb_fetch→LLM→fact_verify，无 ReAct。

详版：架构 §2～§2.4。

---

## 8. 版本路线

| 版本 | 范围 | 要点 |
|------|------|------|
| **MVP** | 生美 | 三舱、persona/竞品、方案包、LangGraph 子图、kb_fetch、分渠道 Skill、Core/Probe |
| **V1.1** | 生美增强 | hybrid_retrieve、trust_asset、scenario-first Core、KB gap、ConsultLog |
| **V2** | B2B 包 | adapt_engine 一源多态、深度内容、完整转化 Dashboard、V2a 偏好、竞品大规模采集 |
| **V2+** | 越用越懂行 | V2b rerank · V2c 可选蒸馏（opt-in） |

---

## 9. 二期能力摘要

> 详版：需求规格 §12 · 架构 §13b · 实施清单 §14

### 9.1 V1.1

- **trust_asset 产线：** case_builder / faq_from_raw → 审过入 KB → 再被 content 引用
- **hybrid_retrieve：** Faiss+BM25 enrich Layer3（不替代 kb_fetch）
- **scenario-first Core 池**、KB 厚度/gap 评分
- **ConsultLog** + 简化归因；效果舱 + 咨询

### 9.2 V2 · B2B

- 行业包 `b2b_manufacturing`；深度内容 Skill（对比/选型/白皮书）
- **adapt_engine：** core_material → 长文/视频脚本/短文案/卖点（fact 继承）
- 政策/参数 fact_verify；竞品官网定向采集
- 完整转化漏斗 Dashboard

### 9.3 V2+ · 偏好学习 / 蒸馏

**原则：** 学偏好与策略排序，**不学事实**；Fact 仍 KB + 人审。

```
监测 + 咨询 + 改稿/驳回 → feedback_aggregator → preference_proposal
  → 效果舱 [采纳] → tenant_preference_profile → 下次 PLAN 排序 ↑
```

| 阶段 | 做什么 |
|------|--------|
| V2a | 高咨询 scenario / 有效渠道 / 常用 angle 统计 |
| V2b | preference_examples → Faiss rerank |
| V2c | 可选蒸馏语气/体例；禁价格/NAP；租户 opt-in |

**合规：** 租户隔离 · 不跨租户 · 不自动改 Fact/发布 · PII 脱敏 · 可重置

---

## 10. MVP 验收

1. 生美 1 店：开店向导 → 一键分析 → 方案包确认 → FAQ+1 小红书 → 托管页 → Core 监测 1 轮  
2. fact_refs 可追溯；禁词拦截；租户隔离；未确认不发布  
3. 小红书 AUTO 失败可 SEMI  

---

## 11. 关联文档

| 文档 | 用途 |
|------|------|
| GEO-需求规格说明书.md | 功能编号、审核清单、API、二期需求 |
| GEO-架构设计说明书.md | 分层、Agent、Orchestrator、表结构 |
| GEO-概要设计说明书.md | 模块数据流、三舱路由 |
| GEO-实施清单.md | 排期与验收 |
| GEO-产品介绍-生美老板版.md | 老板可读 |

路径：`GEO/v2/`

---

*PRD v3.1 — 产品总纲（细节见专项文档）*
