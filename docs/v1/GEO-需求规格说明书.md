# GEO 智能品牌平台 — 需求规格说明书

> **项目名称**：GEO 智能品牌平台（多企业 AI 可见度运营 SaaS）  
> **文档版本**：V1.2  
> **编制日期**：2026-07-02  
> **密级**：内部公开  
> **关联文档**：PRD-v2.md、GEO-概要设计说明书.md、GEO-架构设计说明书.md

---

## 1. 引言

### 1.1 项目背景

在 AI 搜索时代，用户 increasingly 通过豆包、DeepSeek、Kimi、文心一言等获取消费决策建议。生美机构面临新挑战：**品牌曝光从「搜索结果排名」转向「AI 回答是否引用、是否推荐」**。

实地调研（豆包等 AI 回答生美/本地消费问题时）显示，AI 常引用：**携程、去哪儿、本地生活号、抖音**等来源，**地图类信息覆盖偏弱**——说明门店 NAP（名称/地址/电话）一致性、多平台结构化内容建设存在缺口。

### 1.2 核心目标

| 目标 | 说明 |
|------|------|
| **实战化** | 3 步完成：录知识库 → 确认策略与内容 → 发布与监测 |
| **智能化** | Agent 读知识库自动出策略；Skill 执行内容生成与监测 |
| **精准化** | 知识库驱动零幻觉；内容基于客户真实痛点，非关键词堆砌 |
| **可验证** | 监测 AI 提及率、引用来源，形成迭代闭环 |

### 1.3 文档范围

本文档定义功能需求、用户角色、数据实体、非功能需求及 MVP 验收标准。概要设计与架构见配套文档。

**产品边界（不做）：**

- 不承诺 AI 排名第一
- 不全自动发知乎/小红书/点评（平台限制）
- 不代发评价、不刷单
- MVP 不做完整自建 CMS

---

## 2. 总体描述

### 2.1 用户角色

| 角色 | 描述 | 核心诉求 |
|------|------|---------|
| **企业 Owner** | 生美机构老板 | 店被 AI 看到、操作简单、效果可感知 |
| **Admin** | 店长 / 运营 | 管知识库、确认策略、发布内容 |
| **Editor** | 内容编辑 | 改文案、提交审核 |
| **Viewer** | 只读成员 | 看监测报告 |
| **平台管理员** | 平台运营 | 管租户、行业包、Skill、计费 |

**账号模型：** 一企业多账号；一用户可关联多企业（预留代理商）。

### 2.2 技术架构约束

| 约束项 | 要求 |
|--------|------|
| 前端 | Vue 3 + Element Plus（管理台） |
| 后端 | FastAPI，异步任务 |
| AI 交互 | Agent 编排 + Skill 运行时（参考 MCP 思想封装工具） |
| 数据核心 | **企业 KB 为对外发布事实的唯一权威**（Fact/Signal/External 分层）；Skill 不 per-tenant 复制 |
| Agent 编排 | MVP：FastAPI + 轻量 Orchestrator（jobs 状态机）；V1.1：LangGraph |
| 向量检索 | Faiss（V1.1，痛点聚类、variants 同义扩展） |
| 多租户 | 企业数据严格隔离 |
| MVP 行业包 | `beauty_local`（生美默认） |

### 2.3 用户旅程（3 步）

```
Step 1：录入企业知识库（含目标 AI 引擎选择、可选种子关键词）
Step 2：信源诊断 + 痛点/关键词分析 → 策略报告 → 用户确认/修改 → 生成内容
Step 3：发布（AUTO/SEMI/GUIDED）→ 监测 → 迭代
```

**硬性规则：** 策略与对外内容须用户确认后才执行发布。

### 2.4 行业实践共识（外部调研摘要）

| 来源 | 可采纳 | 不采纳 |
|------|--------|--------|
| [16 问 QA](https://zhuanlan.zhihu.com/p/1919030916942107638) | DSS 原则；「AI 喜欢的内容→AI 喜欢的平台」；跨平台常不兼容；AI 应答展现指标 | 关键词堆砌、刷互动 |
| [新榜虚构奶茶实验](https://mp.weixin.qq.com/s/pX6nKkGxHe3y-TQQQ6DjEw) | 先测信源再发文；横评/清单体；发布后即时复测 | 虚构品牌、流量型铺号 |
| [navyum 实战](https://www.cnblogs.com/navyum/articles/19118757) | 信源诊断；总结段优化；分平台发文 | 标题党、保证排名 |

---

## 3. 功能需求详解

### 3.1 模块一：租户与账号（M1）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M1-01 | 用户注册、登录（JWT） | P0 |
| M1-02 | 创建企业（Tenant）、邀请成员 | P0 |
| M1-03 | 角色权限 RBAC（Owner/Admin/Editor/Viewer） | P0 |
| M1-04 | 内容条数钱包 + 监测包月订阅 | P1 |

### 3.2 模块二：企业知识库（M2）

#### 3.2.1 设计原则

- **发布事实唯一权威：** 对外可发布内容中的事实陈述，必须可追溯到 KB 的 Fact 区
- **多源输入、单闸门发布：** 信源诊断、SEO API、爬虫、RawInputs 等可进入 Signal/待确认区，写入 Fact 须用户确认
- 分层：品牌级 + 门店级
- 来源标注：**Fact**（可验证事实）、**Signal**（痛点线索）、**External**（外部采集，待确认）

**KB  freshness（防过期）：**

| 机制 | 说明 | 优先级 |
|------|------|--------|
| M2-F1 | Fact 记录 `updated_at` + 可选 `stale_after_days` | P0 |
| M2-F2 | `beauty_gap_diagnose` 标记「想写但 KB 缺失」 | P0 |
| M2-F3 | 监测发现 NAP 不一致 / 引用旧页 → 提醒更新 KB | P1 |
| M2-F4 | 过期 Fact 生成前警告；fact_verify 失败拒发 | P0 |

#### 3.2.2 知识库结构

```
Enterprise
├── TargetEngines[]（★ 表单最前：客户选择关注的 AI 引擎及优先级）
│     engine: doubao | deepseek | kimi | wenxin | ...
│     priority: primary | secondary | monitor_only
├── SeedKeywords[]（可选：客户指定的爆点/痛点种子词）
├── Brand（品牌名、简介、定位、联系方式）
├── Stores[]（门店：NAP、营业时间、特色项目）
├── Services[]（项目：描述、价格区间、适用人群、注意事项）
├── Cases[]（案例，需真实可验证）
├── Competitors[]（竞品名称、URL）
├── RawInputs[]（客服记录、FAQ、销售话术、用户反馈）
└── KeywordLibrary[]（系统生成 + 人工确认的消费者提问词库）
      type: intent | pain | campaign | local
      phrase: 「东莞皮肤管理哪家好」
      source: raw_input | seo_api | source_diagnose | manual
      frequency_score: 可选
```

**TargetEngines 说明：** 客户人工选择「主攻 / 次攻」引擎（如主攻豆包、次攻 DeepSeek），Agent 按此分配信源诊断、渠道计划与监测配额；非全引擎一刀切。

#### 3.2.3 录入方式

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M2-01 | 表单录入品牌/门店/项目 | P0 |
| M2-02 | 文本粘贴（客服记录、FAQ） | P0 |
| M2-03 | 文件导入（Excel/Word/PDF 解析） | P1 |
| M2-04 | 多门店，门店可覆盖项目与价格 | P1 |
| M2-05 | **TargetEngines 表单**（引擎多选 + 主攻/次攻） | P0 |
| M2-06 | **SeedKeywords** 种子词录入（爆点/痛点） | P1 |
| M2-07 | **KeywordLibrary**：Agent 出词草案 → 用户删改确认后生效 | P0 |
| M2-08 | 文件上传存对象存储（MinIO/OSS；MVP 可用本地目录） | P1 |
| M2-09 | 链接录入预填（官网/美团 URL 解析） | V1.1 |
| M2-10 | 店名自动检索补全（类似 AI 聚合展示） | V1.1 |

### 3.3 模块三：信源诊断、痛点、关键词与策略（M3）

#### 3.3.1 多源痛点输入（优先级）

| 优先级 | 来源 | 说明 |
|--------|------|------|
| P0 | 知识库 RawInputs | 客户自有数据（客服、评价粘贴、FAQ） |
| P1 | 手动补充 | 运营填竞品、常见问题 |
| P2 | SEO/问答 API | 5118、新榜等（非爬虫） |
| P3 | 定向公开页采集 | 竞品官网等（低频、合规） |
| P0+ | source_diagnose 反推 | 各 AI 引用平台与问法（External） |

#### 3.3.1a 痛点挖掘增强（用户画像 / 竞品差异 / 负面信号）

| 编号 | 需求 | 说明 | 优先级 |
|------|------|------|--------|
| M3-P1 | `beauty_pain_mine` | 从 RawInputs(Signal) 聚类痛点、高频问法 | P0 |
| M3-P2 | **用户画像分析** | 从 Signal 归纳决策人群（如：敏感肌年轻白领、产后修复、价格敏感型）；输出 `persona_profiles[]` | P0 |
| M3-P3 | **`beauty_competitor` 竞品差异化** | 对比 KB 中竞品与自身 Service/Case，输出差异点矩阵（项目/价格带/适用人群/地域） | P0 |
| M3-P4 | **负面信号识别（痛点阶段）** | 在 RawInputs/评价粘贴中识别负向 Signal（投诉、顾虑、差评主题），**不替代 V2 全网负面监测** | P0 |
| M3-P5 | 负面 → 选题转化 | 负向 Signal 转为 content_unit 场景（如「会不会越护越敏感」）+ 监测 Prompt | P0 |
| M3-P6 | SEO API / 爬虫补充 | 见上表 P2/P3 | V1.1/V1.2 |

**痛点阶段输出（写入 Strategy 输入）：**

```
pain_analysis {
  pain_clusters[],
  persona_profiles[],      // 用户画像
  competitor_diff[],       // 竞品差异化
  negative_signals[],      // 负向 Signal 摘要（来源标注）
  keyword_library_draft[]
}
```

#### 3.3.2 信源诊断（Strategy 之前，P0）

| 编号 | 需求 | 说明 |
|------|------|------|
| M3-S1 | `source_diagnose` Skill | 按客户选定的 TargetEngines，用 Agent 生成的探测 Prompt 调用各 AI（联网） |
| M3-S2 | 输出信源诊断报告 | 每引擎：引用 URL Top N、平台分布、内容形态、与本地/maps 缺口 |
| M3-S3 | 写入策略输入 | 渠道计划必须引用诊断结果，禁止写死行业渠道表 |

**原则（16 问 Q6）：** 跨平台兼容机会常很小；策略须写清「本问题主攻豆包→小红书/点评；次攻 DeepSeek→知乎/媒体」，由客户 TargetEngines + 实测信源共同决定。

#### 3.3.3 关键词库（与痛点并行）

| 类型 | 来源 | 用途 |
|------|------|------|
| **intent** | SEO/问答 API、信源诊断反推、RawInputs | 监测 Prompt、标题、总结段 |
| **pain** | 痛点挖掘聚类结果 | FAQ、知乎问答体 |
| **campaign** | 客户 SeedKeywords（爆点） | 单篇主推内容主题 |
| **local** | 城市+项目+「附近/哪家」模板 | 本地监测与 GEO 文案 |

**关键词用法（非 SEO 堆砌）：** 关键词进入「监测 Prompt 集 + 标题/首段/总结块」；正文自然出现，须符合 DSS；16 问/Q13 明确关键词堆砌对 GEO 无明显作用。

#### 3.3.4 Agent 需求

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M3-01 | 信源诊断 → 痛点/关键词挖掘 → Orchestrator 策略草案 | P0 |
| M3-02 | Review Agent：合规审查（广告法、生美禁词） | P0 |
| M3-03 | Review Agent：事实审查（是否有 KB 依据） | P0 |
| M3-04 | 策略报告展示；用户可改引擎优先级与关键词 | P0 |
| M3-05 | 知识库提交后 Agent 路由；不在注册时选行业 | P0 |
| M3-06 | DSS 内容评分（Depth / Support / Source） | P0 |
| M3-07 | 产品红线：禁止无 KB 实体的虚构品牌内容 | P0 |

**策略报告含：**

- 业态画像
- **分引擎计划**（主攻/次攻、推荐渠道、探测 Prompt）
- 信源诊断摘要
- 痛点列表 + **KeywordLibrary（待确认）**
- 内容缺口、Skill 计划、监测 Prompt 计划
- DSS 目标与风险提示

#### 3.3.5 策略与 content_unit 融合规则

**生产单元 = 场景问题（content_unit），不是裸关键词。**

```
KeywordLibrary
  → 监测层：intent/local 词 → monitor prompt（分 TargetEngine）
  → 内容层：pain/campaign 聚类为 content_unit（场景问题）
  → 发布层：source_diagnose 为每个 output 匹配渠道

Strategy 输出 content_units[]:
  {
    scenario: "敏感肌能不能做皮肤管理",
    core_intent: pain | campaign,
    variants: ["角质层薄适合做什么项目", "脸一热就红还能做清洁吗"],  # embedding 同义扩展
    fact_refs: [...],
    engine_targets: [doubao, deepseek],
    outputs: [
      { skill: content_faq, channel: hosted_page, keyword_slots: [title, faq_q, summary] },
      { skill: beauty_xhs_note, channel: xiaohongshu },
      { skill: beauty_zhihu_answer, channel: zhihu }
    ],
    monitor_phrase: "敏感肌 皮肤管理 推荐"  # 来自 intent/local
  }
```

**KeywordLibrary UI：** `keyword_mine` 产出 20～40 条草案 → 用户删/改/合并 → 点「确认词库」→ 未确认不进入 Orchestrator 执行。

用户确认时可删词、改主攻引擎、改 content_unit 的 outputs；确认后 Skill 才执行。

### 3.4 模块四：内容工厂（M5）

#### 3.4.1 一源多态

| 内容形态 | 渠道 | 发布模式 |
|---------|------|---------|
| FAQ + Schema | 平台托管页 / 官网 | AUTO |
| 知乎长回答 | 知乎 | SEMI |
| 小红书笔记 | 小红书 | SEMI |
| 项目对比表 | 官网/知乎 | SEMI |
| 点评/美团简介 | 点评/美团 | GUIDED |

#### 3.4.2 功能需求

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M5-01 | 基于知识库 Fact 生成，禁止无来源编造 | P0 |
| M5-02 | 生成后事实核查 + 合规检查 | P0 |
| M5-03 | 用户审核后再进入发布 | P0 |
| M5-04 | 内容版本管理与操作日志 | P1 |
| M5-05 | 内容含**首段结论 + 文末总结块**（含品牌/城市/核心词） | P0 |
| M5-06 | 关键词自然植入（标题/总结/FAQ 问句），禁止堆砌 | P0 |
| M5-07 | 横评/清单体模板（仅真实品牌与 KB 事实） | P1 |
| M5-08 | **多模态**：图文（封面建议）MVP；短视频脚本 V1.1；视频 V2 | P1/V2 |

**DSS 生成约束：**

| 维度 | 要求 |
|------|------|
| D Depth | 直接回答问题，有项目/场景细节 |
| S Support | 价格、时长等必须 fact_refs |
| S Source | 资质、门店、可验证案例 |

### 3.5 模块五：发布中心（M6）

| 模式 | 说明 | MVP |
|------|------|-----|
| AUTO | 平台托管页；可选 WordPress API | P0 |
| SEMI | 导出内容包，一键复制 | P0 |
| GUIDED | 文案 + 「去哪个后台改什么」指引 | P0 |

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M6-01 | 发布任务状态：draft → ready → published | P0 |
| M6-02 | 发布后回填外链 URL（供监测溯源） | P0 |
| M6-03 | 易优 CMS 对接 | V1.1 |
| M6-04 | 托管页默认：FAQPage + LocalBusiness Schema + llms.txt | P0 |
| M6-05 | 发布后 **24h 即时复测** + 每周趋势监测 | P0 |

### 3.6 模块六：监测中心（M7）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M7-01 | 自建监测：DeepSeek、豆包、Kimi、文心 | P0 |
| M7-02 | Prompt 库（行业模板 + Agent 生成 + 用户补充） | P0 |
| M7-03 | 定期执行（建议每周），记录提及率/引用 URL | P0 |
| M7-04 | 监测结果回流策略（缺口分析） | P0 |
| M7-05 | 第三方 GEO 可选接入（per-tenant） | P1 |

**核心指标（对齐 16 问 Q8/Q11）：**

| 指标 | 说明 |
|------|------|
| **AI 应答展现** | 品牌在 AI 回答中出现次数 |
| **引用来源数** | 回答下方带来源链接条数 |
| **信源列表露出** | 过程指标：品牌相关 URL 是否出现在引用列表 |
| 品牌提及率 / 推荐顺位 | 同上细分 |
| Share of Voice | 相对竞品 |
| 情感倾向 | 正/中/负 |

监测 Prompt 集与 KeywordLibrary 的 **intent/local** 词对齐；分 TargetEngines 统计，非合并糊弄。

### 3.7 模块七：报告中心（M8）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M8-01 | 策略报告（Step 2） | P0 |
| M8-02 | 效果报告（趋势、竞品、引用分析、下一步建议） | P0 |

### 3.8 模块八：行业包（M9）

| 编号 | 需求 | 优先级 |
|------|------|--------|
| M9-01 | 加载 `beauty_local` 行业包（**产品/工程预置配置**，非 Agent 现场生成） | P0 |
| M9-02 | 行业包含：Schema 扩展、Skill 清单、Layer 2 Prompt、合规、监测模板、engines 元数据 | P0 |
| M9-03 | 预留其他行业包接口 | P1 |
| M9-04 | MVP 不做重型知识图谱；V1.1 可选 `entity_relations` 显式关系表 | V1.1 |

---

## 4. 数据需求

### 4.1 核心实体

| 实体 | 说明 |
|------|------|
| Tenant | 企业租户 |
| User / Member | 用户与成员关系 |
| KnowledgeBase | 知识库根 |
| TargetEngine / SeedKeyword / KeywordLibrary | 引擎目标与关键词 |
| Brand / Store / Service / Case / Competitor / RawInput | 知识库子实体 |
| SourceDiagnosis | 信源诊断批次结果 |
| Strategy | Agent 输出的策略报告（含 content_units[]） |
| ContentUnit | 场景问题生产单元（scenario + variants + outputs） |
| ContentAsset | 生成的内容资产 |
| PublishTask | 发布任务 |
| MonitorProfile / MonitorRun | 监测配置与批次结果 |
| Job | Agent/Skill 执行任务 |

### 4.2 Skill 工具清单（MVP）

**平台通用：** kb_ingest, entity_extract, fact_verify, compliance_check, content_faq, publish_website, publish_export, monitor_setup, monitor_run, report_generate

**beauty_local：** source_diagnose, keyword_mine, beauty_pain_mine, beauty_competitor, beauty_gap_diagnose, dss_score, beauty_xhs_note, beauty_zhihu_answer, beauty_project_compare, beauty_merchant_copy, beauty_listicle, beauty_local_prompt, beauty_compliance, nap_consistency_check

---

## 5. 非功能性需求

| 类别 | 要求 |
|------|------|
| 性能 | Skill 执行异步化；监测批次后台跑 |
| 安全 | JWT、RBAC、租户隔离；Skill 调用权限校验 |
| 合规 | 生美广告规范；AI 生成内容标识；爬虫 robots 约束 |
| 兼容性 | 管理台适配 Chrome/Edge/Safari 最新版 |
| 可扩展 | 行业包可插拔；Skill 可注册 |

---

## 6. 计费需求（初版）

| 项目 | 方式 |
|------|------|
| 内容 | 按生成/发布条数扣费 |
| 监测 | 包月（基础/标准/高级，按引擎与 prompt 配额分档） |

---

## 7. 验收标准（MVP）

| 编号 | 标准 |
|------|------|
| AC-01 | 1 家生美机构跑通：录库 → 策略确认 → 生成 FAQ + 1 篇小红书 → 托管页发布 → 1 轮监测 |
| AC-02 | 生成内容中参数/价格均可追溯到知识库 Fact |
| AC-03 | 合规审查拦截「最好」「100%有效」等禁词 |
| AC-04 | 监测报告展示至少 4 引擎中 2 引擎以上结果 |
| AC-05 | 企业 A 无法访问企业 B 数据 |
| AC-06 | 未确认策略时，Skill 不自动对外发布 |

---

## 8. 附录

### 8.1 术语

| 术语 | 说明 |
|------|------|
| GEO | Generative Engine Optimization |
| Skill | Prompt + Tools + 约束 的原子能力 |
| 行业包 | 行业可插拔配置（beauty_local 等） |
| NAP | Name / Address / Phone |

### 8.2 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-07-01 | 初版，基于 PRD v1.1 与蒲公英文档结构 |
| V1.1 | 2026-07-02 | 信源诊断、TargetEngines、KeywordLibrary、DSS、分引擎策略、外部调研融合 |
| V1.2 | 2026-07-02 | Fact/Signal/External 分层、content_unit、Faiss、Orchestrator 分阶段、KB freshness |

**批准人签字：** __________  
**日期：** __________
