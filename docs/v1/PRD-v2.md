# GEO 多企业 AI 可见度运营平台 — 产品需求文档 v2.0

> **文档状态**：历史版本，已被 **PRD-v3.md** 取代  
> **更新日期**：2026-07-02  
> **MVP 垂直行业**：生美机构（`beauty_local` 行业包）  
> **关联文档**：GEO-需求规格说明书.md、GEO-概要设计说明书.md、GEO-架构设计说明书.md、GEO-实施清单.md、GEO-产品介绍-生美老板版.md  
> **取代**：PRD-v1.md（v1.1 为历史版本）

---

## 1. 背景与问题

用户 increasingly 通过豆包、DeepSeek、Kimi、文心等 AI 做消费决策。品牌竞争从「被搜索到」转向「**被 AI 引用、被用户采信**」。

**核心问题：**

- 企业不知道 AI 如何描述自己的品牌
- 缺乏结构化、可验证、可引用的内容资产
- 不同 AI 引用不同信源，不知道先测再发
- GEO 效果难监测，难迭代

**我们要做的：**

帮多企业基于各自知识库，完成：**建库 → 信源诊断 → 挖痛点/词库 → Agent 出策略 → Skill 生成内容 → 半自动发布 → 监测 → 迭代**。

**不是什么：**

- 不是批量铺量 AI 软文工厂
- 不承诺 AI 排名第一
- 不虚构品牌、不刷好评
- MVP 不做完整自建 CMS、不做重型知识图谱

---

## 2. 产品定位

| 维度 | 定义 |
|------|------|
| 产品类型 | 多企业 GEO SaaS |
| 一句话 | AI 时代品牌信任资产工厂 |
| 差异化 | KB 驱动零幻觉 + 先测信源再发文 + 分引擎策略 + 监测闭环 |
| 首期行业 | 生美（`beauty_local`；医美规则预留） |
| 扩展 | B2B 制造业、泛本地生活（新增行业包，不改平台内核） |

---

## 3. 目标用户与角色

**MVP 用户：** 单店/连锁皮肤管理、生活美容门店。

| 角色 | 权限概要 |
|------|---------|
| Owner | 全部 |
| Admin | 知识库、策略确认、发布 |
| Editor | 改内容、提交审核 |
| Viewer | 只读报告 |

**账号模型：** 一企业多账号；一用户可关联多企业。

---

## 4. 用户旅程（3 步）

```
Step 1：录入企业知识库
  → 选 TargetEngines（主攻/次攻 AI）
  → 填品牌/门店/项目/RawInputs（可选 SeedKeywords）

Step 2：信源诊断 + 策略 + 内容
  → source_diagnose 测各 AI 引用来源
  → keyword_mine 出词库 → 用户确认
  → Orchestrator 出策略（content_units）→ 用户确认
  → Skill 生成 FAQ/小红书/知乎等 → 用户审核

Step 3：发布 + 监测 + 迭代
  → AUTO/SEMI/GUIDED 发布
  → 24h 复测 + 每周趋势
  → 缺口反馈下一轮策略
```

**硬性规则：** 策略与对外内容须用户确认后才执行发布。

---

## 5. 核心设计决策（v2.0 定稿）

| 议题 | 决策 |
|------|------|
| KB 定位 | **对外发布事实的唯一权威**；分析可多源，发布须过 Fact 闸门 |
| 数据分层 | **Fact**（可发布）/ **Signal**（痛点线索）/ **External**（外部采集，待确认） |
| KB 不全/过期 | gap 检测、updated_at、监测回流、fact_verify 拒发 |
| 信源策略 | **先 source_diagnose，再定渠道**；跨平台兼容常小 |
| TargetEngines | 客户表单选主攻/次攻 AI |
| KeywordLibrary | **Agent 先出词 → 用户删改确认** |
| 内容生产单元 | **content_unit（场景问题）**，一单元多 Skill（FAQ+小红书+知乎） |
| 同义扩展 | variants（Faiss/LLM），防广告腔重复 |
| 关键词用法 | 进监测 Prompt + 标题/总结/FAQ 问句；**禁止正文堆砌** |
| DSS | Depth / Support / Source |
| 产品红线 | 无 KB 实体的虚构品牌内容拒绝生成 |
| 发布 | AUTO 托管页为主；SEMI 导出；GUIDED 点评/美团 |
| 监测 | 自建 4 引擎 + 24h 复测；Otterly 可选 |
| 计费 | 内容按条；监测包月 |
| 痛点输入 MVP | RawInputs + 手动；SEO API V1.1；爬虫 V1.2 |
| 知识图谱 | MVP 不做 Neo4j；V1.1 可选 entity_relations 表 |
| Agent 编排 | **MVP**：FastAPI + jobs 状态机；**V1.1**：LangGraph |
| 向量库 | **Faiss**（V1.1：聚类、variants、语义检索） |
| 对象存储 | MinIO/OSS（MVP 可用本地目录） |
| 行业包 | **产品/工程预置** `beauty_local`；Agent 只消费 |

---

## 6. 系统架构概览

```
展现层     Vue 3 管理台
           ↓
业务层     FastAPI（租户/KB/内容/发布/监测/计费）
           ↓
智能层     Orchestrator + Review Agents + Skill Runtime
           ↓ IndustryPackLoader
行业层     beauty_local（Prompt/Skill/合规/监测模板）
           ↓
基础设施   PostgreSQL + Redis + MinIO/OSS + Faiss(V1.1) + LLM API
```

### 6.1 三层关系

| 层级 | 职责 |
|------|------|
| 平台层 | 租户、KB、Agent、Skill、发布、监测 |
| 行业包层 | Schema、Skill 集、Layer 2 Prompt、合规、engines 模板 |
| 企业层 | 各企业 KB、策略、内容、监测数据 |

### 6.2 行业包（beauty_local）

**由产品/工程设计与维护**，目录示例：

```
industry/beauty_local/
├── schema.json
├── prompts/
├── skills.manifest.json
├── compliance/
├── monitor/
├── engines.json
└── export/
```

Orchestrator 通过 `IndustryPackLoader` 加载；**不在运行时由 Agent 生成行业包**。

---

## 7. 知识库（M2）

### 7.1 结构与分层

```
Enterprise
├── TargetEngines[]（表单最前）
├── SeedKeywords[]（可选）
├── Brand / Stores / Services / Cases / Competitors
├── RawInputs[]（Signal）
└── KeywordLibrary[]（Agent 出词，用户确认）
```

| 类型 | 用途 | 能否直接发布 |
|------|------|:------------:|
| Fact | 价格、地址、项目名 | ✅ |
| Signal | 客服记录、常问 | ❌ 驱动选题 |
| External | 诊断/API/爬虫 | ❌ 确认后入 Fact |

### 7.2 Freshness 机制

- Fact 带 `updated_at`
- `beauty_gap_diagnose` 标记内容缺口
- 监测发现 NAP 不一致 → 提醒更新
- 过期 Fact / fact_verify 失败 → 警告或拒发

### 7.3 录入方式

| 方式 | MVP |
|------|-----|
| 表单 + 文本粘贴 | ✅ P0 |
| 文件上传（→ MinIO/OSS） | P1 |
| 链接录入 / 店名自动补全 | V1.1 |

---

## 8. 信源诊断、词库与策略（M3）

### 8.1 流程

```
TargetEngines + KB
  → source_diagnose（分引擎探测 Prompt）
  → beauty_pain_mine + keyword_mine
  → KeywordLibrary 草案 → 用户确认
  → Orchestrator → Strategy（含 content_units[]）
  → Review（合规+事实）→ 用户确认
  → Skill 执行
```

### 8.2 content_unit 结构

```yaml
content_unit:
  scenario: "敏感肌能不能做皮肤管理"
  variants: ["角质层薄适合做什么项目", ...]
  fact_refs: [service_03, raw_08]
  engine_targets: [doubao, deepseek]
  outputs:
    - { skill: content_faq, channel: hosted_page }
    - { skill: beauty_xhs_note, channel: xiaohongshu }
    - { skill: beauty_zhihu_answer, channel: zhihu }
  monitor_phrase: "敏感肌 皮肤管理 推荐"
```

### 8.3 策略报告含

- 分引擎计划（例：主攻豆包→小红书/点评）
- 信源诊断摘要
- KeywordLibrary + content_units[]
- 内容缺口、监测计划、DSS 目标、风险标注

---

## 9. Skill 与 Agent（M4/M3）

### 9.1 Skill 定义

```
Skill = Prompt 模板 + Tools + I/O Schema + 约束
```

**三层 Prompt：** Layer 1 平台 + Layer 2 行业包 + Layer 3 企业 KB

### 9.2 Agent 分工

| Agent | 职责 |
|-------|------|
| Orchestrator | 读 KB+诊断+词库+行业包 → 策略+content_units |
| Review 合规 | 广告法、生美禁词 |
| Review 事实 | 是否有 KB 依据 |

**路由：** 不在注册时选行业；KB 提交后识别业态 → 匹配 `beauty_local`。

### 9.3 MVP Skill 清单

**平台：** kb_ingest, entity_extract, fact_verify, compliance_check, content_faq, publish_website, publish_export, monitor_setup, monitor_run, report_generate

**beauty_local：** source_diagnose, keyword_mine, beauty_pain_mine, beauty_gap_diagnose, dss_score, beauty_xhs_note, beauty_zhihu_answer, beauty_project_compare, beauty_merchant_copy, beauty_listicle, beauty_compliance, nap_consistency_check

---

## 10. 内容工厂（M5）

- 一源多态：同一 fact_refs → FAQ / 小红书 / 知乎
- 首段结论 + 文末总结块
- fact_verify + compliance + 用户审核
- 多模态：图文 MVP；短视频脚本 V1.1；视频 V2

---

## 11. 发布中心（M6）

| 模式 | 渠道 | MVP |
|------|------|-----|
| AUTO | 平台托管页（Schema + llms.txt）；可选 WordPress | ✅ |
| SEMI | 知乎、小红书导出 | ✅ |
| GUIDED | 点评、美团指引 | ✅ |

发布后回填 URL；24h 即时复测。

---

## 12. 监测中心（M7）

**引擎：** DeepSeek、豆包、Kimi、文心（自建 P0）；Otterly 等（可选 P1）

**指标：**

| 指标 | 说明 |
|------|------|
| AI 应答展现 | 品牌出现在回答中次数 |
| 引用来源数 | 回答下方来源链接条数 |
| 信源列表露出 | 品牌 URL 是否被引用 |

Prompt 集与 KeywordLibrary 的 intent/local 对齐；分 TargetEngines 统计。

---

## 13. 技术选型摘要

| 模块 | 选型 |
|------|------|
| 前端 | Vue 3 + Element Plus + Pinia |
| 后端 | FastAPI |
| 数据库 | PostgreSQL |
| 缓存/队列 | Redis |
| 对象存储 | MinIO / 云 OSS（MVP 可本地） |
| Orchestrator | MVP：jobs 状态机；V1.1：LangGraph |
| 向量 | **Faiss**（V1.1） |
| LLM | 多模型可配置（国内 API 为主） |

**试点最小闭环：** 1～2 家门店，FastAPI + 3 个 Skill（source_diagnose → keyword_mine → content_faq），不必先上 LangGraph/Faiss。

---

## 14. 外部调研共识

| 来源 | 采纳 | 不采纳 |
|------|------|--------|
| 16 问 QA | DSS；分平台；跨平台常不兼容；AI 应答展现 | 关键词堆砌 |
| 新榜实验 | 先测信源；清单体；24h 复测 | 虚构品牌 |
| navyum | 信源诊断；总结段优化 | 标题党 |

---

## 15. MVP 范围

### 15.1 P0 必做

- [ ] 多租户 + RBAC
- [ ] KB（TargetEngines、RawInputs、Fact/Signal）
- [ ] source_diagnose + KeywordLibrary 确认
- [ ] Orchestrator + Review + content_units
- [ ] FAQ + 小红书 + 知乎 + 托管页 AUTO
- [ ] 4 引擎监测 + 24h 复测
- [ ] beauty_local 行业包

### 15.2 排除

- 全自动发知乎/小红书/点评
- 负面全网监测、B2B 包、CRM 归因、重型 KG、完整 CMS

### 15.3 版本路线

| 版本 | 内容 |
|------|------|
| MVP | 上文 P0 |
| V1.1 | LangGraph、Faiss、SEO API、WordPress、链接录入、entity_relations |
| V2 | B2B 行业包、负面监测、CRM |
| V3 | 多 region、媒体 API |

---

## 16. 计费（初版）

| 项目 | 方式 |
|------|------|
| 内容 | 按条（FAQ/小红书/知乎各 1 条，权重可配） |
| 监测 | 包月（基础/标准/高级，按引擎与 prompt 配额） |

内容钱包与监测订阅分离。

---

## 17. 验收标准

| # | 标准 |
|---|------|
| AC-01 | 1 家生美跑通：录库→诊断→策略确认→FAQ+1 小红书→托管页→监测 |
| AC-02 | 内容参数/价格可追溯到 Fact |
| AC-03 | 合规拦截禁词 |
| AC-04 | 至少 2 引擎监测结果 |
| AC-05 | 租户隔离 |
| AC-06 | 未确认策略不自动发布 |

**第一版最小闭环：**

> 录库（选豆包主攻）→ 信源诊断 → 策略确认 → FAQ + 1 小红书 → 托管页 → 24h 监测

---

## 18. 仍开放事项

1. content_unit 确认页 UI
2. 多模态视频供应商
3. SEO API 首选（5118/新榜等）
4. 托管页自定义域名
5. 各内容形态条数权重表

---

## 19. 术语

| 术语 | 说明 |
|------|------|
| GEO | Generative Engine Optimization |
| Industry Pack | 行业可插拔配置包 |
| Skill | Prompt + Tools + 约束 |
| content_unit | 场景问题生产单元 |
| DSS | Depth / Support / Source |
| NAP | Name / Address / Phone |

---

## 20. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0 | 2026-07-02 | 整合 V1.1 技术文档 + 四答定稿 + 架构决策（Faiss、Fact 分层、content_unit、Orchestrator 分阶段） |
| v1.1 | 2026-07-01 | 见 PRD-v1.md（历史） |

---

*本文档为活文档。详细模块设计、接口、排期见 `技术/` 目录。*
