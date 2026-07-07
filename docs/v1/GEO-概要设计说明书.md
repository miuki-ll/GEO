# GEO 智能品牌平台 — 概要设计说明书

> **项目名称**：GEO 智能品牌平台  
> **文档版本**：V1.2  
> **编制日期**：2026-07-02  
> **编制地点**：广东省  
> **关联文档**：GEO-需求规格说明书.md、GEO-架构设计说明书.md、PRD-v2.md

---

## 1. 引言

### 1.1 编写目的

本文档对 GEO 智能品牌平台进行**高层次概要设计**，基于《需求规格说明书》，明确系统模块划分、核心业务流程、数据流向及关键技术逻辑，作为详细设计与代码实现的指导文件。

### 1.2 项目背景与目标

帮多企业（MVP 为生美机构）在 AI 搜索时代建立「被 AI 看见、被用户信任」的品牌内容体系。通过知识库、Agent 编排、Skill 工具链，实现 **分析 → 生成 → 发布 → 监测 → 迭代** 闭环。

### 1.3 核心设计原则

| 原则 | 说明 |
|------|------|
| **AI 原生** | Agent 驱动策略与执行，非简单「AI 写稿按钮」 |
| **知识库为本** | KB 为**对外发布事实的唯一权威**；分析可多源，发布须过 Fact 闸门 |
| **Fact/Signal/External** | Fact 可发布；Signal 驱动选题；External 待确认后入 Fact |
| **Skill 为本** | 能力单元化，Orchestrator 按需调度，不按企业复制 Skill |
| **行业可插拔** | 平台稳定，行业差异收敛到 Industry Pack |
| **分引擎策略** | 跨平台兼容常小；客户选主攻/次攻引擎 + 信源诊断驱动渠道 |
| **关键词为意图** | KeywordLibrary 服务监测与内容任务，非 SEO 堆砌 |

---

## 2. 系统总体设计

### 2.1 系统架构图（逻辑四层）

```
展现层     Vue 3 管理台（知识库、策略、内容、发布、监测、报告）
           ↓
业务层     FastAPI（租户、知识库、内容、发布、监测、计费）
           ↓
智能层     Orchestrator Agent + Review Agents + Skill 运行时
           ↓
数据层     PostgreSQL（业务） + Faiss（向量，V1.1） + Redis（缓存/队列） + 对象存储（MinIO/OSS）
```

### 2.2 模块划分

| 子系统 | 核心功能 | 对应需求 |
|--------|---------|---------|
| **用户中心** | 注册登录、企业、成员、权限 | M1 |
| **知识库中心** | 品牌/门店/项目/RawInput 管理 | M2 |
| **策略中心** | 信源诊断、Orchestrator、Review、关键词融合、策略确认 | M3 |
| **内容工厂** | Skill 生成、审核、版本 | M5 |
| **发布中心** | AUTO / SEMI / GUIDED | M6 |
| **监测中心** | Prompt 库、批次监测、第三方可选 | M7 |
| **报告中心** | 策略报告、效果报告 | M8 |
| **行业包服务** | beauty_local 加载与配置 | M9 |
| **管理后台** | 租户、Skill 注册、计费、审计 | M10 |

### 2.3 与「AI 蒲公英部落」架构的对照

| 蒲公英（参考） | GEO（本项目） |
|---------------|--------------|
| 简历为核心实体 | **知识库**为核心实体 |
| Skills 图谱 → 人岗匹配 | **Skill 工具链** → 内容/监测/发布 |
| MCP Tools | Skill = Prompt + Tools + 约束 |
| 求职驾驶舱 | **GEO 运营驾驶舱**（策略+监测） |
| 实战任务看板 | 发布任务看板 + 监测迭代 |

---

## 3. 核心功能模块设计

### 3.1 知识库中心

**设计目标：** 构建企业 AI 可见度的「事实与信号」底座。

**数据结构：**

- `Tenant`：企业租户
- `TargetEngine`：客户选择的 AI 引擎及 priority（primary/secondary）
- `SeedKeyword`：客户指定爆点/痛点种子词
- `KeywordLibrary`：intent/pain/campaign/local 词库，带来源与频次
- `Brand`：品牌信息
- `Store`：门店（NAP、营业时间、门店级项目）
- `Service`：服务项目
- `Case`：案例
- `Competitor`：竞品
- `RawInput`：原始输入（客服、FAQ），标注为 **Signal**
- `ExternalCandidate`：外部采集（诊断/API/爬虫），**待确认**后晋升 Fact
- `Fact`：可验证事实，带 `source_ref`、`updated_at`

**关键流程：**

```
用户录入 KB（含 TargetEngines、可选 SeedKeywords）
  → kb_ingest / entity_extract
  → source_diagnose（按 TargetEngines 探测信源）
  → keyword_mine + beauty_pain_mine（并行）
  → Orchestrator 融合 → Strategy 草案
  → Review → 用户确认（可改引擎/关键词）
  → Skill 执行
```

### 3.2 信源诊断（source_diagnose）

**设计目标：** 发布前回答「AI 从哪抄答案」，避免写死渠道表。

```
输入：TargetEngines[] + Agent 生成的探测 Prompt（来自城市/项目/品类）
过程：对各引擎联网提问 → 解析 cited_urls / 平台分布
输出：SourceDiagnosis {
  per_engine: { top_domains[], content_formats[], map_gap: bool }
}
```

### 3.3 关键词库（keyword_mine）

```
RawInputs + SEO API + SourceDiagnosis 反推 + SeedKeywords
  → 聚类去重（V1.1：Faiss 辅助 variants 同义扩展）
  → KeywordLibrary[] 草案
  → 用户确认 → 写入 Strategy.keyword_plan
```

**与策略融合：** 每个 **content_unit（场景问题）** 映射多 Skill 产出 + monitor_prompt；keyword 仅作 variants 与槽位，不作独立生产单元。

### 3.4 策略中心（Agent）

**设计目标：** 读知识库，输出可确认的策略，不直接对外发布。

**Orchestrator 输入/输出：**

```
输入：KnowledgeBase + SourceDiagnosis + KeywordLibrary
      + IndustryPack(beauty_local) + MonitorHistory(可选)
输出：Strategy {
  business_profile,
  engine_plan[],
  keyword_plan[],
  content_units[],    // 场景问题 + variants + 多 Skill outputs
  pain_points, content_gaps,
  channel_plan, skill_plan, monitor_plan,
  compliance_level, dss_targets
}
```

**行业包加载：** `IndustryPackLoader` 读取 `industry/beauty_local/` 预置配置（Prompt、禁词、Skill 清单）；**由产品/工程维护，Orchestrator 只消费，不现场生成行业包。**

**Review 流程：**

```
Strategy 草案 → 合规 Review → 事实 Review → 策略报告（含风险标注）
  → 用户确认/修改 → 冻结 Strategy → 触发 Skill 执行
```

**路由逻辑：** 不在注册时选行业；知识库提交后 Agent 识别生美/单店/连锁等，匹配 `beauty_local`。

### 3.5 痛点挖掘（beauty_pain_mine）

**多源合并流程：**

```
RawInputs(Signal) ──┐
SeedKeywords ───────┤
手动补充 ───────────┼→ 聚类/去重 → 痛点 + KeywordLibrary
SEO API ────────────┤
定向爬虫(可选) ───────┘
```

### 3.6 内容工厂

**一源多态：**

```
KnowledgeBase Facts + keyword_plan 条目
  → content Skill（注入 intent/pain 词到标题/总结，非堆砌）
  → dss_score + fact_verify + compliance_check
  → ContentAsset（待审核）
```

**多模态：** MVP 图文（封面 hint）；V1.1 短视频脚本；V2 视频生成（非 MVP）。

### 3.7 发布中心

| 模式 | 实现 |
|------|------|
| AUTO | `publish_website` → 托管页（Schema + llms.txt）；可选 WordPress |
| SEMI | `publish_export` → JSON/Markdown 内容包 + 复制按钮 |
| GUIDED | 同上 + 操作 checklist（点评/美团字段说明） |

### 3.8 监测中心

```
monitor_setup：KeywordLibrary.intent/local → 分引擎 Prompt 集
monitor_run：按 TargetEngines 定时 + 发布后 24h 即时复测
  → AI 应答展现、引用来源数、信源露出
  → gap_analyze → Orchestrator
```

**第三方：** MonitorProfile.integrations[] 可选 Otterly 等。

---

## 4. 数据设计概要

### 4.1 核心实体关系

```
Tenant (1) ---- (N) UserMember
Tenant (1) ---- (1) KnowledgeBase
KnowledgeBase (1) ---- (N) Store / Service / Case / Competitor / RawInput
Tenant (1) ---- (N) Strategy
Strategy (1) ---- (N) ContentAsset
ContentAsset (1) ---- (0..1) PublishTask
Tenant (1) ---- (1) MonitorProfile
MonitorProfile (1) ---- (N) MonitorRun
Tenant (1) ---- (N) Job（Agent/Skill 任务）
```

### 4.2 关键数据表（逻辑）

| 表 | 说明 |
|----|------|
| tenants | 企业 |
| users / tenant_members | 用户与成员 |
| brands / stores / services / cases / competitors | 知识库实体 |
| target_engines / seed_keywords / keywords | 引擎目标与词库 |
| source_diagnoses | 信源诊断 JSON |
| strategies | 策略 JSON + 状态（draft/confirmed） |
| content_assets | 内容 + fact_refs + 版本 |
| publish_tasks | 渠道、模式、状态、external_url |
| monitor_profiles / monitor_runs / monitor_results | 监测 |
| jobs | 异步任务 |
| billing_wallets / subscriptions | 计费 |

---

## 5. 接口设计概要

### 5.1 RESTful API（前端 → 后端）

| 方法 | 路径（示例） | 说明 |
|------|-------------|------|
| POST | /api/auth/login | 登录 |
| POST | /api/tenants | 创建企业 |
| CRUD | /api/tenants/{id}/kb/* | 知识库 |
| POST | /api/tenants/{id}/source-diagnose | 信源诊断 |
| POST | /api/tenants/{id}/analyze | 触发 Orchestrator（含痛点/关键词/策略） |
| GET/PUT | /api/strategies/{id} | 策略报告、确认 |
| POST | /api/strategies/{id}/execute | 确认后执行 Skill |
| CRUD | /api/content-assets | 内容审核 |
| POST | /api/publish-tasks | 发布 |
| GET | /api/monitor/runs | 监测结果 |
| GET | /api/reports/* | 报告 |

### 5.2 Skill 内部接口（Agent 运行时）

不直接暴露给前端；由 Agent 服务统一调度：

```
invoke_skill(skill_name, tenant_id, params, strategy_id) → SkillResult
```

---

## 6. 安全与性能设计

### 6.1 安全性

- JWT 认证 + RBAC
- 所有 API 带 tenant_id 隔离
- Skill 调用校验：只能读当前 tenant 知识库
- 爬虫：robots.txt、频率限制、定向 URL 白名单

### 6.2 性能

- Skill 执行、监测批次：**异步队列**（Redis/Celery 或等价）
- 热点：行业包配置、Prompt 模板 Redis 缓存
- LLM 调用：流式返回策略生成进度（SSE，可选）

---

## 7. 部署与运维

| 环境 | 方案 |
|------|------|
| 开发 | Docker Compose：FastAPI + Vue + PostgreSQL + Redis |
| 生产 | K8s 或云托管（后期） |
| 监控 | API 日志 + LLM 调用/token 统计 |

---

## 8. 总结

本平台以**企业知识库**为核心，通过 **Orchestrator + Review + Skill** 实现 GEO 闭环；行业差异收敛到 `beauty_local` 行业包。MVP 聚焦生美机构，跑通「录库 → 策略 → 内容 → 托管页发布 → 监测」全链路。

下一步：详细数据库表结构、Skill 协议定义、API OpenAPI 文档。

**批准人签字：** __________  
**日期：** __________

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-07-01 | 初版 |
| V1.1 | 2026-07-02 | 信源诊断、关键词库、分引擎策略、DSS |
| V1.2 | 2026-07-02 | Fact/Signal/External、content_unit、Faiss、Orchestrator 分阶段、行业包说明 |
