# GEO 本地商家 AI 可见度平台 — 概要设计说明书 v2.1

> **版本**：V2.1 | **日期**：2026-07-16
> **关联**：[G-L1-PRD-v2.md](G-L1-PRD-v2.md) · [G-L2-架构设计说明书.md](G-L2-架构设计说明书.md) · [G-L1-需求规格说明书.md](G-L1-需求规格说明书.md)

---

## 0. 设计原则

| 原则 | 说明 |
|------|------|
| **KB 为本** | 发布事实唯一权威；Fact/Signal/External 三层 |
| **LLM 动态生成** | 探针/画像/词库/scenario/竞品由 LLM 实时产出，行业包只给规则簿 |
| **scenario-first** | 生产单元 = 场景问句；篇数 = 结果非目标 |
| **先选 AI 再测信源** | 用户选 target_engines → source_diagnose → 信源地图 |
| **content_unit** | 1 scenario × 1 渠道 × 1 Skill |
| **信源权重混合** | 内部固定 0.6 + 探针实测 0.4 |
| **RAG 双步** | 步骤5 生成时自动切片 · 步骤6 检测时验证可检索性 |
| **人必确认** | 策略+草稿合并一次人闸门；策略更新草案 |
| **行业包薄配置** | 规则簿 9 项 + few-shot 3 组 · 新增品类 0 管道改动 |

---

## 1. 四层架构

```
展现层   Vue3+Vite+TS+Element Plus 管理台
        └─ 三舱：onboarding / strategy-pack / outcomes

业务层   FastAPI + Pydantic v2
        └─ 10 模块 API：onboarding / diagnosis / strategy_pack / content
           publish / monitoring / outcomes / kb / enterprise / auth

智能层   Agent ToB 三层
        ├─ L1 LLM Gateway：4 EngineAdapter（豆包/DeepSeek/Kimi/文心）
        ├─ L2 Harness：Celery jobs + LangGraph 子图(onboarding) + ReAct
        │              + Skill Runtime(固定链 kb_fetch→LLM→verify · 无ReAct)
        └─ L3 垂域：IndustryPack 规则簿（禁词/合规/渠道/CTA/few-shot）

数据层   PostgreSQL + Redis + Faiss(per-tenant) + OSS
        └─ 22 张表 · enterprise_id 隔离 · Alembic 迁移
```

---

## 2. 8 步管道模块数据流

### 2.1 步骤1 · 入驻建库

```
Input  → 用户填写的 NAP/项目/竞品/核心优势/RawInputs + 可选 target_engines + 品类
         ↓
Process → POST /onboarding/run
          - 写入 Enterprise / Brand / Store / Service（Fact 直写，不靠种子）
          - 激活 IndustryPack 规则簿 → 注入租户配置（禁词/合规/渠道/CTA）
          - 生成托管页 + Schema(LocalBusiness+FAQPage) + llms.txt
         ↓
Output  → KB 就绪 · target_engines[] 就绪 · 托管页 URL
```

### 2.2 步骤2 · 诊断 agent

```
Input  → KB Facts + target_engines[] + 行业包 probe_few_shot + competitor_types
         ↓
Process → onboarding_graph (Celery Job):
          DIAGNOSE 节点:
            1. LLM 生成探针问句（品类+商圈+店名+价格+probe_few_shot）
            2. EngineAdapter 逐条测试（仅 target_engines 范围）
            3. 采集：提及率/顺位/失真度/竞品挤占度
            4. 信源地图：采集 URL→域名聚合→排行榜→缺口报告
            5. 实体健康度检测
            6. 赛道判定（空白/突围/防御）
            7. LLM 竞品拆解：用户竞品名+URL→EngineAdapter对比探测→差异简报
         ↓
Output  → SourceDiagnosis[] 入库 · GEO 健康报告 · T0 基线数据
```

### 2.3 步骤3 · 意图词库

```
Input  → RawInputs(KBSignal) + 探针结果(SourceDiagnosis) + SEO API + LLM
         ↓
Process → 四源汇聚:
          1. RawInputs → exact 去重 → embedding → Faiss per-tenant 聚类(≥0.85)
             → LLM 簇命名 → 归入四层
          2. 探针反推：从 AI 答案中提取高频品类词/场景词 → 归入四层
          3. SEO/问答 API：5118/百度指数/知乎热榜 → 归入四层
          4. LLM 直接生成：输入品类+商圈+服务+探针结果 → 四层输出
         ↓
          → 四源合并 → 去重 → LLM 自动分层 → 用户确认/编辑
         ↓
Output  → Keyword[] 入库（四层标注 · 来源标注 · 租户隔离）
          → 高频问句 → FAQ draft
          → 同步到 Core 监测池槽位
```

### 2.4 步骤4 · 策略生成

```
Input  → 诊断报告 + 四层词库(确认版) + KB Facts + 行业包规则簿
         ↓
Process → StrategyPackBuilder:
          A. persona_analyze:
             LLM(RawInputs+探针结果+用户填写+persona_hint)
             → buyer_personas[] + content_layout_plan[]
          B. competitor_analyze:
             LLM(诊断竞品拆解+用户竞品URL)
             → competitor_profiles[] + differentiation_brief[] + content_gaps[]
          C. scenario 候选生成:
             LLM(词库选型+场景层 + 画像 + 竞品差异 + scenario_few_shot)
             → 8-10 条候选 → Faiss 去重 → 推荐给用户勾选 ≤5
          D. 信源权重计算:
             每渠道 weight = 内部固定模型(0.6) + 探针实测模型(0.4)
          E. 词库展示(折叠 · 四层 · 标来源)
         ↓
Output  → StrategyPackDraft（五区 · 待闸门①确认）
```

### 2.5 步骤5 · 内容工厂

```
Input  → 确认的 scenario × 渠道 × fact_refs
         ↓
Process → SkillRuntime（固定链 · 不用 ReAct）:
          1. kb_fetch(fact_refs) → 拉取 KB Fact
          2. LLM 生成 → 7段式模板填充 → 分渠道 Skill 格式化
          3. RAG 切片（生成时自动做）:
             - 300-800 字/块
             - 独立标题+摘要+关键词
             - 前200字前置结论
             - 三级标题+有序列表+定义块
         ↓
Output  → ContentDraft[] 入库（含切片标记 · draft 状态）
```

### 2.6 步骤6 · 内容检测

```
Input  → ContentDraft[] + KB Facts + 行业包 forbidden_words + compliance_checklist
         ↓
Process → 检测链（固定链 · 不用 ReAct）:
          ① fact_verify:     价格/NAP/项目描述/案例/竞品 匹配 KB
          ② 禁词:            行业包 + 广告法 + AI生成标识
          ③ 交叉验证:        卖点一致 + ≥3平台同源 + 电话/地址一致
          ④ 实体一致性:      店名/电话/卖点 100% 一致
          ⑤ RAG 可检索性:    切片独立可读 · 结论前置 · 摘要关键词齐全
         ↓
          → 不通过: 标红 + 告警类型 → 打回步骤5
          → 通过: draft → ready
         ↓
Output  → ContentDraft[ready] · 待闸门
```

### 2.7 人闸门

```
Input  → 策略摘要 + 方案包 + ContentDraft[ready][]
         ↓
Process → 合并展示:
          「基于您选择的{AI平台}，测试出的引用渠道有{信源测试模型}，
            根据 GEO 健康报告将生成{0.6+0.4混合权重}的篇数。
            内容为{方案包摘要}。具体内容如下：{草稿列表}」
         ↓
          → [确认] → draft→ready→进发布队列 · approval_log 写入
          → [打回] → draft → 回到步骤5
         ↓
Output  → ContentDraft[ready] → PublishTask 队列
```

### 2.8 步骤7 · 发布

```
Input  → ContentDraft[ready][]
         ↓
Process → PublishDispatcher:
          AUTO:   托管页(API直发) + 搜狐号/头条号(白皮书合作)
          SEMI:   小红书/知乎(OAUTH→失败降级 导出包)
          GUIDED: 点评/美团(优化稿+操作指引)
         ↓
Output  → PublishTask[]（content_asset_id + 渠道 + 时间 + 模式）
          → 触发 24h 后 Core 复测
```

### 2.9 步骤8 · 监控迭代

```
Input  → target_engines[] + Core/Probe 池 + T0 基线
         ↓
Process → Celery Beat 定时:
          每周 monitor_run: EngineAdapter 对 Core ~20 + Probe ≤10 逐条测试
          T1 = 发布 24h 后采集
          Δ 对比(T1-T0): 提及率变化 + 幻觉率变化 + 信源露出变化
         ↓
          临界检测(连续2周):
            提及率<30% | 信源露出=0% | 连降>20%
            → gap_analyze → StrategyUpdateDraft → 人确认 → 迭代
         ↓
          幻觉修复:
            发现错误 → 生成官方标准说明 → 高权重渠道覆盖 → 复测
         ↓
Output  → MonitorResult[] · OutcomeSnapshot[] · 效果舱 Dashboard
```

---

## 3. 三舱路由与前端模块

### 3.1 路由映射

```
舱1 懂我:
  /onboarding        → views/onboarding/Index.vue     (开店向导)
  /strategy-pack     → 含词库确认区                  (意图词库编辑)
                      → 含健康报告区                  (诊断结果展示)

舱2 定方案:
  /strategy-pack     → views/strategy/Index.vue       (方案包五区)
  /content/drafts    → views/content/Drafts.vue       (草稿审核 · 人闸门)

舱3 出结果:
  /outcomes          → views/outcomes/Index.vue       (效果舱默认页)
  /publish/tasks     → views/publish/Tasks.vue        (发布任务)
  /monitor           → views/monitor/Index.vue        (监测看板)
```

### 3.2 前端状态流

```
onboarding/Index.vue
  └─ POST /onboarding/run → onboardingStore.taskId
       └─ SSE GET /onboarding/status/{taskId} → progress_pct
            └─ 100% → router.push('/strategy-pack?draft=1')

strategy/Index.vue
  └─ GET /strategy-pack/draft → 五区渲染
       └─ POST /strategy-pack/confirm → 闸门①
            └─ router.push('/content/drafts')

content/Drafts.vue
  └─ GET /content/drafts → 草稿列表 + 策略摘要
       └─ POST /content/drafts/bulk-approve → 闸门②
            └─ router.push('/publish/tasks')
                 └─ 自动触发发布 → router.push('/outcomes')

outcomes/Index.vue
  └─ GET /outcomes/dashboard → 效果舱 Dashboard
       └─ T0/T1 对比 · 四层漏斗 · 转化闭环
```

---

## 4. 数据流关键节点

### 4.1 租户隔离流

```
所有 API 请求:
  Authorization: Bearer <JWT>
  → get_current_user() 解析: user_id + enterprise_id
  → service 层: filter(Model.enterprise_id == current.enterprise_id)
  → 跨租户访问 → HTTP 403
```

### 4.2 行业包注入流

```
入驻时:
  POST /onboarding/run { industry: "beauty_local" }
  → enterprise.industry_pack = "beauty_local"
  → IndustryRegistry.get("beauty_local") → BeautyLocalPack()
  → 后续所有步骤通过 get_industry_pack(enterprise.industry_pack) 获取规则
```

### 4.3 EngineAdapter 联动流

```
用户修改 target_engines:
  PUT /enterprise { target_engines: ["豆包", "Kimi"] }
  → Enterprise.target_engines 更新
  → 下次诊断/监测: EngineAdapter 仅启用 ["doubao", "kimi"]
  → 探针/监测结果仅覆盖这两个引擎
```

---

*概要设计说明书 v2.1 · 对齐 PRD-v2.1 + ARCHITECTURE v2.0*
