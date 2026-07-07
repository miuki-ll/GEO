# GEO 多企业 AI 可见度运营平台 — 实施清单

> **文档版本**：V1.2  
> **编制日期**：2026-07-02  
> **关联文档**：PRD-v2.md、GEO-需求规格说明书.md、GEO-概要设计说明书.md  
> **MVP 行业**：生美机构（`beauty_local` 行业包）

---

## 1. 文档说明

本文档将产品方案拆解为**可执行的实施清单**，按用户旅程与系统模块组织，供开发排期与验收对照。

**一句话目标：** 多企业 GEO SaaS — KB 为发布事实权威，完成「挖痛点 → 出策略 → 生成内容 → 发布 → 监测 → 迭代」闭环。

---

## 2. 总流程概览

### 2.1 用户视角（3 步）

| 步骤 | 用户做什么 | 系统做什么 |
|------|-----------|-----------|
| Step 1 | 录入 / 上传企业信息 | 建知识库、解析实体、标注来源 |
| Step 2 | 确认策略与内容 | Agent 分析、Review、生成多版本内容 |
| Step 3 | 发布并查看效果 | 发布、监测 AI 可见度、出报告、迭代 |

### 2.2 系统内部（7 段，V1.1）

```
① 建库        知识库 + TargetEngines（选 AI）+ 可选 SeedKeywords
② 信源诊断    按选定 AI 探测 Prompt → 统计引用平台
③ 挖词痛点    RawInputs + 手动（MVP）；SEO API/爬虫 V1.1+
④ 出策略      分引擎计划 + content_units[] → 用户确认
⑤ 产内容      Skill 生成（DSS + 关键词植入标题/总结）
⑥ 发布        托管页 AUTO / 其他 SEMI·GUIDED
⑦ 监测迭代    24h 即时复测 + 每周趋势 → 再回 ④
```

**关键原则：** 策略必须经用户确认后才执行内容生成与发布。

---

## 3. 阶段 0：平台基础（开发先做）

| # | 任务 | 交付物 | 优先级 |
|---|------|--------|--------|
| 0.1 | 多企业租户 | 注册、登录、企业创建 | P0 |
| 0.2 | 一企业多账号 | Owner / Admin / Editor / Viewer | P0 |
| 0.3 | 数据隔离 | tenant_id 全链路隔离 | P0 |
| 0.4 | 计费骨架 | 内容条数钱包 + 监测包月订阅字段 | P1 |
| 0.5 | Agent / Skill 框架 | Skill 注册、调度、执行日志 | P0 |
| 0.6 | 行业包加载 | MVP 加载 `beauty_local` | P0 |
| 0.7 | 异步任务 | Skill 执行、监测批次后台跑 | P0 |
| 0.8 | Orchestrator MVP | FastAPI + jobs 状态机（V1.1 迁 LangGraph） | P0 |

---

## 4. 阶段 1：知识库（M2）— 一切起点

### 4.1 设计原则

- **发布事实权威：** 对外内容事实必须可追溯 KB Fact 区
- **多源输入、单闸门发布：** Signal/External 可分析，写入 Fact 须确认
- **分层结构：** 品牌级 + 门店级
- **来源标注：** Fact / Signal / External（待确认）
- **禁止幻觉：** 无 Fact 依据不得发布；fact_verify 失败拒发
- **Freshness：** Fact 带 updated_at；过期警告；gap 检测

### 4.2 知识库数据结构

```
Enterprise（企业）
├── TargetEngines[]（★ 表单最前）
│     engine, priority: primary | secondary
├── SeedKeywords[]（可选爆点/痛点种子词）
├── Brand / Stores[] / Services[] / Cases[] / Competitors[]
├── RawInputs[]（Signal）
└── KeywordLibrary[]（系统生成，用户确认）
      type: intent | pain | campaign | local
```

### 4.3 数据分类

| 类型 | 说明 | 示例 | 用途 |
|------|------|------|------|
| **Fact** | 可验证事实 | 价格、地址、项目名 | 生成内容必须引用 |
| **Signal** | 痛点线索 | 客户常问、抱怨 | 痛点分析、content_unit 选题 |
| **External** | 外部采集 | 诊断/API/爬虫结果 | 待确认后晋升 Fact |

示例：

```
Fact:   「补水管理」价格 298–498 元，来源：kb:service_01
Signal: 「很多客户问敏感肌能不能做光子」，来源：kb:raw_chat_12
```

### 4.4 录入方式（MVP）

| 方式 | 内容 | 优先级 |
|------|------|--------|
| 表单填写 | 品牌、门店、项目 | P0 |
| 文本粘贴 | 客服记录、FAQ | P0 |
| 文件上传 | Excel / Word / PDF | P1 |
| 批量导入 | 模板 CSV | P1 |

### 4.5 实施任务

| # | 任务 | 验收标准 | 优先级 |
|---|------|---------|--------|
| 1.0 | TargetEngines 表单 | 多选引擎 + 主攻/次攻 | P0 |
| 1.1 | 品牌信息 CRUD | 可增删改品牌基础字段 | P0 |
| 1.2 | 多门店 CRUD | 支持 1 品牌 N 门店，NAP 完整 | P0 |
| 1.3 | 项目 / 服务 CRUD | 生美项目字段 + 关联门店 | P0 |
| 1.4 | 竞品录入 | 名称、URL、备注 | P0 |
| 1.5 | RawInputs 录入 | 文本粘贴 + 来源类型标注 | P0 |
| 1.6 | Fact / Signal 标注 | 导入时或解析后自动 / 手动分类 | P0 |
| 1.7 | 案例录入 | 背景、方案、结果，带来源 | P1 |
| 1.8 | 文件导入解析 | kb_ingest Skill 解析上传文件 | P1 |
| 1.9 | 实体抽取 | entity_extract 从 RawInputs 抽实体 | P1 |
| 1.10 | SeedKeywords 录入 | 客户爆点/痛点种子词 | P1 |
| 1.11 | KeywordLibrary UI | Agent 出词 → 用户删改确认 | P0 |
| 1.12 | 对象存储接入 | MinIO/OSS 或 MVP 本地目录 | P1 |

---

## 5. 阶段 2：信源诊断 — KB 就绪后、策略前（P0）

### 5.1 逻辑

```
读取 TargetEngines（客户选的 AI）
  → Agent 根据 KB 生成探测 Prompt（城市+项目+品类）
  → 对各引擎联网提问
  → 解析 cited_urls / 平台分布
  → SourceDiagnosisReport
```

### 5.2 实施任务

| # | 任务 | 验收标准 | 优先级 |
|---|------|---------|--------|
| 2.0 | source_diagnose Skill | 分引擎输出 Top 引用平台 | P0 |
| 2.0b | 探测 Prompt 生成 | 基于 KB 自动产 5–10 条/引擎 | P0 |
| 2.0c | 诊断报告页 | 可视化：如「豆包→点评/抖音；地图弱」 | P0 |

---

## 6. 阶段 3：挖痛点 + 关键词库

### 6.1 多源采集（按优先级）

| 优先级 | 输入方式 | 说明 | 是否爬虫 |
|--------|---------|------|---------|
| P0 | 客户自有数据 | RawInputs | 否 |
| P0+ | 客户 SeedKeywords | 爆点/痛点种子 | 否 |
| P1 | 手动补充 | 运营填竞品、补充常见问题 | 否 |
| P2 | SEO / 问答 API | 5118、新榜等关键词、问答热词 | **不是爬虫** |
| P3 | 定向公开页采集 | 竞品官网公开页（低频、合规） | 是 |

**原则：** 有客户数据用客户数据；没有再用 API；爬虫只做补充。

### 6.2 关键词类型

| 类型 | 来源 | 用途 |
|------|------|------|
| intent | SEO API、RawInputs | 监测 Prompt、标题 |
| pain | 痛点聚类 | FAQ、知乎 |
| campaign | SeedKeywords | 单篇主推 |
| local | 城市+项目模板 | 本地监测 |

**注意：** 关键词进标题/首段/总结/FAQ 问句；**禁止正文堆砌**（16 问/Q13）。

### 6.3 执行 Skill

- `beauty_pain_mine` — 痛点
- `keyword_mine` — 词库合并去重

### 6.4 实施任务

| # | 任务 | 验收标准 | 优先级 |
|---|------|---------|--------|
| 3.1 | P0 痛点挖掘 | 从 RawInputs 聚类 | P0 |
| 3.2 | keyword_mine | 产出 KeywordLibrary 草案 | P0 |
| 3.3 | 用户确认词库 | Agent 出 20～40 条 → 删改确认后进策略 | P0 |
| 3.4 | SEO API 接入 | V1.1 | P2 |
| 3.5 | 定向爬虫 | V1.2 白名单低频 | P3 |
| 3.6 | Faiss 向量索引 | variants 同义扩展、痛点聚类 | V1.1 |

---

## 7. 阶段 4：Agent 出策略 — 用户必须确认

### 7.1 Agent 分工

```
Orchestrator Agent（MVP：jobs 状态机；V1.1：LangGraph）
  读 KB + SourceDiagnosis + KeywordLibrary（已确认）+ 行业包
  → engine_plan + content_units[]
  → Review → 用户确认

Review Agents（策略确认前）
  ├── 合规审查：广告法、生美禁词
  └── 事实审查：策略是否有知识库依据

用户确认 + 人工修改
  ↓
Skill 运行时执行
```

### 7.2 策略报告内容

- 业态画像
- **分引擎计划**（例：主攻豆包→小红书/点评；次攻 DeepSeek→知乎）
- 信源诊断摘要
- KeywordLibrary（已确认）及 **content_units[]**（场景问题 + 多 Skill outputs）
- 内容缺口、Skill 计划、监测计划
- DSS 目标、风险标注

### 7.3 content_unit 融合规则

```
content_unit（场景问题）
  scenario + variants[]（Faiss/LLM 同义扩展，防广告腔）
  outputs[]: FAQ + 小红书 + 知乎（同一 fact_refs）
  monitor_phrase: 来自 intent/local 词库
```

用户确认时可改 outputs、删 unit、改主攻引擎。

### 7.4 实施任务

| # | 任务 | 验收标准 | 优先级 |
|---|------|---------|--------|
| 4.1 | Orchestrator 融合诊断+词库 | 输出 engine_plan + content_units[] | P0 |
| 4.2 | 合规/事实 Review | P0 |
| 4.3 | 策略报告页（可编辑引擎/关键词） | P0 |
| 4.4 | dss_score Skill | P1 |
| 4.5 | 虚构品牌拦截 | 无 KB 实体则拒绝生成 | P0 |

---

## 8. 阶段 5：Skill 生成内容

### 8.1 一源多态 + 关键词植入

同一知识库事实 → 多种内容形态：

| Skill | 产出 | 发布模式 | 计费 |
|-------|------|---------|------|
| content_faq | 官网 FAQ + Schema | AUTO | 1 条 |
| beauty_xhs_note | 小红书笔记 | SEMI | 1 条 |
| beauty_zhihu_answer | 知乎回答 | SEMI | 1 条 |
| beauty_project_compare | 项目对比表 | SEMI / AUTO | 1 条 |
| beauty_merchant_copy | 点评 / 美团简介 | GUIDED | 1 条 |

| beauty_listicle | 横评/清单（仅真实品牌） | SEMI | 1 条 |

**格式要求：** 首段结论 + 文末总结块；关键词仅 title/summary/FAQ 问句优先。

**多模态：** 图文 MVP；短视频脚本 V1.1；视频 V2。

### 8.2 内容生成约束

每条生成内容必须：

1. 引用知识库 Fact（`fact_refs`）
2. 跑事实核查（fact_verify）
3. 跑生美合规检查（beauty_compliance / compliance_check）
4. DSS 评分（Depth / Support / Source）
5. 用户审核后再进入发布

### 8.3 Skill 清单（MVP 增补）

| Skill | 说明 | 优先级 |
|-------|------|--------|
| source_diagnose | 信源诊断 | P0 |
| keyword_mine | 关键词库 | P0 |
| dss_score | DSS 评分 | P1 |
| beauty_listicle | 横评清单体 | P1 |
| nap_consistency_check | NAP 一致性 | P1 |

（其余 Skill 见 V1.0 清单）

### 8.4 实施任务

| # | 任务 | 验收标准 | 优先级 |
|---|------|---------|--------|
| 5.1 | Skill 运行时 | 按 Strategy content_units 调度 | P0 |
| 5.2 | FAQ 生成 | 带 Schema，fact_refs 完整 | P0 |
| 5.3 | 小红书笔记生成 | 标题 + 正文 + 标签 | P0 |
| 5.4 | 知乎回答生成 | 问答体，事实可溯源 | P0 |
| 5.5 | 内容审核工作台 | 用户审阅、修改、通过 | P0 |
| 5.6 | 项目对比表 | P1 | P1 |
| 5.7 | 点评 / 美团文案 | GUIDED 包 | P1 |

---

## 9. 阶段 6：发布（M6）

### 9.1 三种发布模式

| 模式 | 说明 | 渠道 | MVP |
|------|------|------|-----|
| **AUTO** | API 自动发布 | 平台托管页、WordPress | ✅ |
| **SEMI** | 内容包 + 一键复制 / 导出 | 知乎、小红书、公众号 | ✅ |
| **GUIDED** | 文案 + 操作指引 | 点评、美团、地图 POI | ✅ |

### 9.2 官网 AUTO 方案（已定）

| 方案 | MVP |
|------|-----|
| **平台托管页**（主推） | ✅ |
| WordPress REST API | ✅ 可选 |
| 易优 CMS | V1.1 |
| 自建 CMS | ❌ 不做 |

### 9.3 发布任务字段

- 渠道、模式、内容引用
- 状态：draft → ready → published / failed
- 发布时间、外链 URL（回填供监测溯源）

### 9.4 实施任务

| # | 任务 | 验收标准 | 优先级 |
|---|------|---------|--------|
| 6.1 | 平台托管页 | 项目页 + FAQ + LocalBusiness Schema | P0 |
| 6.2 | 托管页 AUTO 发布 | 一键发布，返回 URL | P0 |
| 6.3 | SEMI 导出包 | 知乎 / 小红书格式导出 | P0 |
| 6.4 | GUIDED 指引包 | 点评 / 美团文案 + 操作步骤 | P1 |
| 6.5 | WordPress 对接 | REST API 推送（可选） | P1 |
| 6.6 | 发布任务管理 | 状态流转、URL 回填 | P0 |
| 6.7 | llms.txt + Schema | 托管页技术 GEO | P0 |

### 9.5 MVP 不做

- 全自动发知乎 / 小红书 / 点评
- 代发评价、刷单

---

## 10. 阶段 7：监测 + 迭代（M7）

### 10.1 监测逻辑

```
KeywordLibrary.intent/local → 分 TargetEngine 的 Prompt 集
  → 发布后 24h 即时复测
  → 每周趋势监测
  → AI 应答展现 / 引用来源数 / 信源露出
  → 反馈 Orchestrator
```

### 10.2 核心指标

| 指标 | 说明 |
|------|------|
| AI 应答展现 | 品牌出现在 AI 回答中次数 |
| 引用来源数 | 回答下方来源链接条数 |
| 信源列表露出 | 品牌 URL 是否被引用 |

| 7.1 | 监测 Prompt 配置 | 来自策略 + 模板 + 用户补充 | P0 |
| 7.2 | 4 引擎监测执行 | monitor_run 定时批次 | P0 |
| 7.3 | 结果解析存储 | 提及、排名、引用 URL | P0 |
| 7.4 | 效果报告 | 趋势图 + 竞品对比 | P0 |
| 7.5 | 24h 发布后复测 | 发布后 24h 即时 probe | P0 |
| 7.6 | 监测 → 策略闭环 | 缺口反馈 Orchestrator | P1 |
| 7.7 | 第三方监测接口 | per-tenant 可选配置 | P2 |

---

## 11. 全链路关系图（V1.1）

```
KB（TargetEngines + SeedKeywords + 业务事实）
  ↓
source_diagnose（分引擎）
  ↓
beauty_pain_mine + keyword_mine → KeywordLibrary（用户确认）
  ↓
Orchestrator → engine_plan + content_units[]
  ↓
Review → 用户确认
  ↓
Skills（DSS + 关键词槽位）→ 审核 → 发布
  ↓
monitor（24h + weekly）→ 迭代
```

---

## 12. 开发顺序（MVP 排期建议）

| 顺序 | 模块 | 交付物 | 里程碑 |
|------|------|--------|--------|
| 1 | 租户 + 账号 | 注册、建企业、邀成员 | 能登录 |
| 2 | 知识库 + TargetEngines | 选 AI + 建库 | 能选引擎 |
| 3 | source_diagnose | 分引擎信源报告 | 能测信源 |
| 4 | keyword_mine + 痛点 | 词库确认 | 能出词 |
| 5 | Orchestrator + Review | 分引擎策略 | 能出策略 |
| 5 | 内容 Skill | FAQ + 小红书 + 知乎 | 能生成内容 |
| 6 | 发布中心 | 托管页 AUTO + 导出 SEMI | 能发布 |
| 7 | 监测中心 | 4 引擎 + 基础报告 | 能监测 |
| 8 | 闭环 | 监测 → 回策略 | 能迭代 |
| 9 | 计费 | 内容条数 + 监测包月 | 能计费 |

### 12.1 第一版最小闭环

> **录库（含选豆包主攻）→ 信源诊断 → 出策略 → FAQ + 1 篇小红书 → 托管页 → 24h 监测**

---

## 13. 计费实施

| 用户动作 | 计费方式 |
|---------|---------|
| 生成 / 发布 1 条内容 | 扣 1 条（FAQ、知乎、小红书等各算 1 条，权重可配） |
| 监测服务 | 包月订阅 |

### 13.1 监测分档

| 档位 | 监测方式 |
|------|---------|
| 基础版 | 自有监测（DeepSeek / 豆包 / Kimi / 文心），prompt 有限额 |
| 标准版 | 自有 + 更高 prompt 配额 + 更长历史 |
| 高级版 | 自有 + 可选第三方 GEO（Otterly 等） |

架构上：**内容钱包与监测订阅分离**。

---

## 14. MVP 验收清单（P0）

### 14.1 平台

- [ ] 多企业注册、一企业多账号、基础 RBAC
- [ ] 企业数据 tenant 隔离

### 14.2 知识库

- [ ] TargetEngines 表单（主攻/次攻）
- [ ] source_diagnose 信源报告
- [ ] KeywordLibrary 确认流程
- [ ] RawInputs 录入 + Fact / Signal 标注
- [ ] 竞品录入

### 14.3 Agent

- [ ] Orchestrator 出策略报告
- [ ] 合规 Review + 事实 Review
- [ ] 用户确认后才执行 Skill

### 14.4 内容

- [ ] FAQ + 小红书 + 知乎生成
- [ ] fact_refs + 事实核查 + 生美合规
- [ ] 用户内容审核

### 14.5 发布

- [ ] 平台托管页 AUTO
- [ ] 知乎 / 小红书 SEMI 导出
- [ ] 发布任务状态 + URL 回填

### 14.6 监测

- [ ] 国内 4 引擎自建监测
- [ ] 基础效果报告
- [ ] beauty_local 行业包加载

### 14.7 MVP 排除项

- [ ] 全自动发知乎 / 小红书 / 点评
- [ ] 负面全网监测
- [ ] B2B 制造业行业包
- [ ] CRM 转化归因
- [ ] 完整自建 CMS

---

## 15. 仍开放事项

1. content_unit 确认页 UI（勾选 FAQ/小红书/知乎 outputs）
2. 多模态（视频）优先级与供应商
3. SEO API 首选供应商（V1.1）
4. 平台托管页自定义域名
5. 链接录入 / 店名自动补全（V1.1）

---

## 16. 文档修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-07-01 | 初版 |
| V1.1 | 2026-07-02 | TargetEngines、信源诊断、KeywordLibrary、分引擎策略、外部调研 |
| V1.2 | 2026-07-02 | Fact/Signal/External、content_unit、Faiss、Orchestrator 分阶段、章节编号修正 |

---

*本文档为活文档，随开发迭代更新。*
