# GEO 多企业 AI 可见度运营平台 — PRD v4.0

> **状态**：产品定稿基线 | **日期**：2026-07-04  
> **MVP 行业**：生美 `beauty_local`  
> **详版**：`GEO-需求规格说明书.md` · `GEO-架构设计说明书.md` · `GEO-概要设计说明书.md`

---

## 0. 第一性原理（项目锚点）

> 面向**特定目标人群**，匹配**真实问答场景**，输出**信息增量**与**差异化价值**，建立**品牌专业信任**，完成**咨询与成交转化**。

| ❌ 禁止 | ✅ 方向 |
|--------|--------|
| 批量伪原创 | KB + fact_verify |
| 追求发文数量 | **scenario 驱动**，条数=结果非目标 |
| 一稿通发 | 分渠道 Skill（V2 一源多态） |
| 只盯 AI 提及 | 可见度 + 信任 + **可验证转化** |
| 关键词堆砌 | scenario-first；词库仅辅助监测 |

**价值公式：** 内容价值 ≈ 信息增量 × 品牌信任度  
**North Star：** AI 信任资产 → 分渠道可见度 → 转化闭环（非软文工厂）

**可量化指标（MVP 周会）：**

| 指标 | 说明 |
|------|------|
| Core 提及率 | 主攻 engine，Core 池含已选 scenario |
| 托管页表单数 | 第一方转化信号 |
| 单店闭环天数 | 开店向导提交 → 首次发布 → 效果舱 1 轮监测 |

---

## 1. 产品定义

AI 时代选购参考转向豆包/DeepSeek/Kimi/文心。**GEO（Generative Engine Optimization，生成式引擎优化）** = 让 AI 能引用、能采信你的真实品牌信息。

| 维度 | 说明 |
|------|------|
| 产品 | 多企业 GEO SaaS |
| 差异化 | KB 零幻觉 · 先选 AI 再测信源 · scenario 分渠道 · Core/Probe 监测 · 七段转化闭环 |
| 不是什么 | 软文工厂、保证第一、虚构品牌、刷好评、铺量 KPI |

---

## 2. 转化闭环 · 三舱 · 对外 3 步

> 复杂分析封装在系统内；用户 **2 次确认闸门**（方案包 + 草稿审）。详版：需求规格 §3。

### 2.1 闭环七段（摘要）

```
录入 KB → 信源诊断 → 定 scenario → 生产+双审 → 分渠道发布 → AI 监测 → 转化反馈/迭代草案
         ↑________________补 KB / 改 scenario________________|  ↑____策略草案（人确认）____|
```

| 阶段 | 三舱 | 人闸门 |
|------|------|--------|
| 录入+诊断 | 舱1 | — |
| 定 scenario | 舱2 方案包 | **① 确认并生成** |
| 生产 | 舱2 草稿 | **② 通过** |
| 发布+监测+迭代 | 舱3 效果舱 | 策略草案确认 |

### 2.2 三舱对照

| 舱 | 用户说 | 系统后台 |
|----|--------|----------|
| **舱1 懂我** | 告诉我店的信息 | 建库 → 诊断 → 痛点/词库 → 画像 → 竞品 |
| **舱2 定方案** | 看方案、确认出稿 | PLAN → EXECUTE → 机器审 → **草稿审** |
| **舱3 出结果** | 发布、看效果 | 发布 → 监测 → 效果舱 → 迭代入口 |

### 2.3 对外 3 步

**Step 1 · 开店向导** — 一次提交：选 AI、店信息、目标客户、竞品、核心优势、RawInputs → `[开始分析]` → 后台 job 链（进度条）。

**Step 2 · 方案包 + 草稿审**

1. **方案包**（一页，见 §2.4）→ `[确认并生成草稿]`
2. **草稿列表** → 逐条或批量 `[通过]`

**Step 3 · 效果舱** — 发布（AUTO→失败 SEMI）+ Dashboard（AI KPI + 托管页流量 + 发布追踪；V1.1 +咨询归因）。

**铁律：** 无 Fact 不发布；**条数 = 已选 scenario 数**（≤5）；临界只出草案、人确认后迭代。

### 2.4 方案包 Strategy Pack

| 区块 | 来源 | 用户操作 |
|------|------|----------|
| **A 画像** | persona_analyze | 确认 persona + content_layout_plan |
| **B 竞品** | competitor_content_analyze | 确认/编辑 differentiation_brief |
| **C 场景** | pain + campaign + 差异化 | **勾选 2～5 个 scenario** |
| **D 渠道** | source_weight_builder | 调 weight；**承接 scenario 数**（非「写几篇」） |
| **E 展开** | keyword_mine、freshness | 词库（监测辅助）、KB 黄条（折叠） |

**API：** `GET strategy-pack/draft` · `POST strategy-pack/confirm` · `GET content-drafts` · `POST content-drafts/bulk-approve`

### 2.5 开店向导字段

| 步 | 字段 | 写入 |
|----|------|------|
| 1 | TargetEngines | target_engines |
| 2 | 品牌/门店/项目 | KB Fact |
| 3 | 目标客户（模板多选） | persona 种子 |
| 4 | 竞品 + 可选链接 | competitors[] |
| 5 | 一句话核心优势 | brand.differentiator |
| 6 | RawInputs | Signal |

提交 → `POST onboarding/run` → `DIAGNOSE → PAIN → PERSONA → COMPETITOR` → 跳转方案包。

### 2.6 效果舱与转化

| 指标 | MVP | V1.1 |
|------|-----|------|
| AI 提及 / 信源露出 | Core | ✅ |
| 托管页 PV / 表单 | ✅ | ✅ |
| 发布 content_asset_id 追踪 | ✅ | ✅ |
| 咨询 / ConsultLog 归因 | — | ✅ |
| 策略建议 | 临界→草案 | + 高提及零咨询 |

---

## 3. 已定决策（速查）

| 议题 | 决策 |
|------|------|
| 生产单元 | **scenario**；1 scenario × 1 渠道 × 1 Skill |
| KB | Fact/Signal/External；FAQs[]；`kb_updated_at` + freshness（MVP）；厚度/gap（V1.1） |
| 三舱 UX | 开店向导 + 方案包 + 效果舱（无独立策略/权重路由 MVP） |
| 词库 | Agent+SEO 出词→确认；**辅助监测槽位**，非生产起点 |
| 正文取数 | MVP `kb_fetch(fact_refs)`；V1.1 hybrid_retrieve enrich |
| 监测 | Core + Probe；**MVP：词库 + 已选 scenario 同步 Core 子集**；V1.1 全量 scenario-first |
| 发布 | 托管页 AUTO；**小红书/知乎默认 SEMI**，AUTO 为可选尝试 |
| Agent | L1 jobs + L2 LangGraph 子图 + L3 ReAct；正文 Skill **无 ReAct** |
| 转化 | MVP：content_id + 托管页；V1.1：ConsultLog + 简化归因 |
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

**trust_asset（信任资产）：** MVP 用 Cases/FAQs/NAP；V1.1 独立产线 case_builder / faq_from_raw → 审过入 KB → 再被 content 引用。

---

## 5. 核心能力（MVP）

### 5.1 系统管道

```
onboarding/run
  → source_diagnose → pain/keyword_mine → persona_analyze → competitor_content_analyze
  → strategy_pack/draft → 用户 confirm（闸门①）
  → GAP_ANALYZE → PLAN → EXECUTE_SKILLS → 机器审
  → 草稿审（闸门②）→ PUBLISH（记 content_asset_id）→ monitor → 效果舱
  → [临界] gap_analyze 草案 → 人确认 → 迭代
```

### 5.2～5.7

信源诊断、persona、竞品、痛点词库、content_unit、kb_fetch、审核发布监测 — **详版见需求规格 §6～§9**。

**content_unit 要点：**

```yaml
content_unit:
  core_intent: pain | campaign | differentiation
  scenario: "敏感肌能不能做皮肤管理"   # 最小生产单元
  channel, topic_angle, target_persona
  fact_refs[], output: { skill, publish_mode }
```

### 5.8 审核 · 发布 · 监测 · 迭代

| 环节 | MVP |
|------|-----|
| **机器审** | fact_verify、compliance、beauty_compliance、禁堆砌、禁虚构品牌 |
| **人工审** | 草稿工作台 → `ready` |
| **发布** | 托管页 AUTO；小红书/知乎 AUTO→SEMI；点评 GUIDED |
| **监测** | Core（~20/engine）+ Probe（≤10/engine） |
| **迭代** | Core 2 周临界 → 策略更新**草案**（人确认） |

审核清单：需求规格 §7.3。

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

### 7.1 Agent ToB 三层

| 层 | GEO | 状态 |
|----|-----|------|
| L1 通用 LLM | LLM Gateway | MVP |
| L2 Harness | jobs + LangGraph + ReAct | MVP |
| **L3 垂域** | 行业包 + Skill + KB + 三舱 | **壁垒 · 重心** |

**正文 Skill：** 固定链 kb_fetch→LLM→fact_verify，无 ReAct。详版：架构 §2.1。

---

## 8. 版本路线

### 8.0 MVP-A · 首发最小路径（优先验收）

> 完整 P0 见需求规格；**首发建议按 MVP-A 交付**，其余 P0 项可并行但非阻塞上线。

| 项 | MVP-A |
|----|-------|
| 诊断 | **主攻 engine 全量**；次攻可选/降频 |
| scenario | **2 个**（标准包 3 个） |
| 渠道 | 托管页 AUTO + **1 渠道 SEMI**（小红书或知乎） |
| 监测 | 主攻 engine Core 1 轮 + 已选 scenario 进 Core |
| 分析 | onboarding 链保留；竞品可简化 |

### 8.1 版本表

| 版本 | 范围 | 要点 |
|------|------|------|
| **MVP** | 生美 | 三舱、scenario、MVP-A 路径、kb_fetch、Core/Probe |
| **V1.1** | 生美增强 | trust_asset、hybrid_retrieve、全量 scenario Core、KB 厚度分、ConsultLog |
| **V2** | B2B 包 | adapt_engine、深度内容、完整转化 Dashboard、V2a 偏好 |
| **V2+** | 越用越懂行 | V2b rerank · V2c 可选蒸馏（opt-in） |

---

## 9. 二期能力摘要

> 详版：需求规格 §16 · 架构 §13b · 实施清单 §14

### 9.1 V1.1

- trust_asset 产线、hybrid_retrieve、scenario-first Core、KB 厚度/gap、ConsultLog + 简化归因

### 9.2 V2 · B2B

- `b2b_manufacturing`、adapt_engine、政策/参数 fact_verify、完整转化漏斗

### 9.3 V2+ · 偏好学习

**原则：** 学偏好与策略排序，**不学事实**；Fact 仍 KB + 人审。V2a→V2b→V2c；租户 opt-in；可重置。

---

## 10. MVP 验收

对齐需求规格 **AC-01～AC-17**，最小路径：

1. 生美 1 店：开店向导 → 方案包确认 → FAQ+1 小红书 → 托管页 → Core 监测 1 轮  
2. fact_refs 可追溯；禁词拦截；租户隔离；2 次人闸门  
3. 小红书 AUTO 失败可 SEMI；publish_task 带 content_asset_id  

---

## 11. 关联文档

| 文档 | 用途 |
|------|------|
| GEO-需求规格说明书.md | **功能唯一基线**：FR/AC、闭环、审核、API、版本 |
| GEO-架构设计说明书.md | 分层、Agent、Orchestrator、表结构 |
| GEO-概要设计说明书.md | 模块数据流、三舱路由 |
| GEO-实施清单.md | 排期、检测、验收勾选 |
| GEO-产品介绍-生美老板版.md | 老板可读 |
| 优化.md | 多角色评估 |
| **二期.md** | 暂未落地的优化项 |

路径：`GEO/v4/`

---

*PRD v4.1 — 已吸收优化.md 可落地项*
