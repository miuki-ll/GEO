# GEO 双人任务拆分与分工说明

> **版本**：v1.2 | **日期**：2026-07-16  
> **关联**：[G-L1-需求规格说明书.md](G-L1-需求规格说明书.md) · [G-L1-PRD-v2.md](G-L1-PRD-v2.md) · [G-L3-API契约.md](G-L3-API契约.md) · [G-L3-实施清单.md](G-L3-实施清单.md) · [G-L2-架构设计说明书.md](G-L2-架构设计说明书.md) · **[G-L3-开发进度.md](G-L3-开发进度.md)（git 同步进度表）**

---

## 0. 文档说明

本文约定 **2 人并行开发 MVP** 时的角色边界、代码归属、输入输出契约、**跨人依赖闸门** 与排期。

| 原则 | 说明 |
|------|------|
| 竖切流水线 | 按「上游懂我 / 下游定方案+出结果」切，少抢同一文件 |
| 契约交接 | 跨人只通过 API / JSON fixture / 表字段交接，不互相改对方 service 内部 |
| 契约源 | 字段以 [G-L3-API契约.md](G-L3-API契约.md) 为准；改字段必须先改契约再改代码 |
| 统一信封 | `{ "code": 0, "data": {}, "msg": "ok" }` · JWT Bearer · `enterprise_id` 租户隔离 |
| **依赖显式化** | 任一任务若依赖对方未完成项，必须标 `WAIT_FOR`；Agent 到此步须停下来提示对方开发者 |
| **进度同步** | 任务状态只写在 [G-L3-开发进度.md](G-L3-开发进度.md)，变更后 `commit` + `push`，双方以该文件为准 |

**角色代号：**

| 代号 | 称呼 | 一句话 |
|------|------|--------|
| **开发者 A** | 上游 | 让店能登录、建库、跑出诊断和词库 |
| **开发者 B** | 下游 | 让方案能确认、写出稿、发出去、看出效果 |

---

## 0.1 给 Agent 的依赖协议（必读）

### 标记语义

| 标记 | 含义 | Agent 行为 |
|------|------|------------|
| `依赖: 无` | 不依赖对方轨，可独立做 | 直接实现 |
| `依赖: 己方 Ax/Bx` | 只依赖自己前面的任务 | 先完成前置己方任务 |
| `WAIT_FOR: Ax / Bx` | **硬依赖对方任务**；无对方交付则联调/真接不可继续 | **停止越界实现对方模块**；输出下方「提示话术」给对方开发者；本侧可用 fixture/mock 继续 UI 或单测 |
| `MOCK_OK` | 硬依赖存在，但允许用 fixture 先做 | 可用 §2.3 fixture 继续；须在注释/TODO 标明「待联调替换」 |
| `NOTIFY: Ax / Bx` | 本任务完成后会 unblock 对方 | 完成后主动提示对方「可开始某任务」 |
| `GATE` | 联调闸门；双方都完成后才算过线 | 检查清单全绿再宣称联调通过 |

### Agent 遇到 `WAIT_FOR` 时必须做的事

1. **不要**去改对方目录里的代码（见 §1.1）。
2. **向当前会话用户明确说出**：被阻塞的任务号、等待的对方任务号、缺什么交付物。
3. **复制并展示**对应任务下的「Agent 提示对方」话术（可微调人名）。
4. 若任务标了 `MOCK_OK`：可用 fixture 继续本侧工作，并留下 `TODO(WAIT_FOR: …)`。
5. 若任务**未**标 `MOCK_OK`：停在闸门，只做文档/契约/单测骨架，不伪造对方业务写入。

### Agent 提示话术模板（通用）

```text
【跨人依赖 · 请通知开发者 {对方}】
我方正在实现：{本方任务号} {本方任务名}
被阻塞原因：需要对方先完成 {对方任务号} {对方任务名}
需要对方交付：
  - {交付物1}
  - {交付物2}
验收看：{验收标准一句话}
契约：[G-L3-API契约.md] / 本文 §{章节}
在对方交付前：我方{继续用 fixture / 暂停真接联调}
```

---

## 1. 分工总览

| 维度 | 开发者 A · 上游 | 开发者 B · 下游 |
|------|-----------------|-----------------|
| **产品范围** | 舱1「懂我」+ 平台底座 | 舱2「定方案」+ 舱3「出结果」 |
| **管道步骤** | 1 入驻 · 2 诊断 · 3 词库 | 4 策略 · 5 内容 · 6 检测 · 人闸门 · 7 发布 · 8 监控 · 效果舱 |
| **对应 FR** | FR-ON / FR-DG / FR-KW | FR-SP / FR-CF / FR-CK / FR-GT / FR-PB / FR-MN / FR-CV |
| **后端模块** | auth · enterprise · kb · industry · llm gateway · faiss · onboarding · diagnosis · keywords | strategy_pack · content · publish · monitoring · outcomes |
| **前端页面** | `/login` `/register` `/onboarding` `/knowledge-base` `/settings` | `/strategy-pack` `/content/drafts` `/publish/tasks` `/monitor` `/outcomes` |
| **Agent** | `onboarding_graph`（DIAGNOSE→PAIN→PERSONA→COMPETITOR）· 探针 LLM | SkillRuntime（kb_fetch→LLM→输出）· 5 项检测链 · Celery Beat 监测 |
| **表归属** | enterprises / users / brands / stores / services · kb_* · source_diagnoses · keywords · agent_tasks（入驻）· faiss_indexes | scenarios · strategy_pack_drafts / strategy_packs · content_assets / content_drafts · approval_logs · publish_tasks · monitor_* · outcome_snapshots · hosted_page_events |
| **共享只读** | IndustryPack 规则簿（A 维护，B 只调用） | LLM Gateway（A 维护，B 只调用 `chat()`） |

### 1.1 代码目录归属（禁止越界改）

| Owner | 可改路径 |
|-------|----------|
| **A** | `backend/app/api/v1/user/auth.py` · `enterprise.py` · `kb.py` · `onboarding.py` · `diagnosis.py`（及 keywords 相关） · `service/auth_service.py` · `kb_*.py` · `diagnosis_service.py` · `agents/graphs/onboarding/` · `agents/industry/` · `core/llm/` · `core/embedding.py` · `frontend/src/views/onboarding/` · `knowledge-base/` · `settings/` · `Login.vue` · `Register.vue` · `api/auth.ts` · `api/enterprise.ts` · `api/kb.ts` · `api/onboarding.ts` |
| **B** | `backend/app/api/v1/user/strategy_pack.py` · `content.py` · `publish.py` · `monitoring.py` · `outcomes.py` · `service/strategy_service.py` · `scenario_service.py` · `content_service.py` · `publish_service.py` · `monitor_service.py` · `dashboard_service.py` · Skill / 检测相关 · `frontend/src/views/strategy/` · `content/` · `publish/` · `monitor/` · `outcomes/` · `api/strategy.ts`（及下游 API 封装） |
| **共建（PR 双方 review）** | `docs/G-L3-API契约.md` · `backend/app/models/`（新字段）· `backend/app/schemas/`（跨域字段）· Alembic 迁移 |

---

## 1.2 依赖总表（Agent 速查）

> 读任务前先查本表。凡含 `WAIT_FOR` 的行，实现到该步必须提示对方。

### A 任务依赖

| 任务 | 己方前置 | 跨人依赖 | 完成后 NOTIFY |
|------|----------|----------|---------------|
| A0 IndustryPack | — | 无 | **NOTIFY B**：禁词/渠道默认可调用（B4） |
| A1 JWT/租户 | — | 无 | **NOTIFY B**：可挂鉴权调下游 API |
| A2 KB CRUD | A1 | 无 | **NOTIFY B**：`kb_facts.id` 可供 `fact_refs`（B3） |
| A3 LLM Gateway | — | 无 | **NOTIFY B**：可调用 `chat()`（B1/B3） |
| A4 Faiss | A1 | 无 | **NOTIFY B**：词库/scenario 去重可复用（B1） |
| A5 入驻建库 | A0 A1 A2 | 无 | — |
| A6 SSE | A5 | 无 | — |
| A7 诊断+T0 | A3 A5 A6 | 无 | **NOTIFY B**：`diagnosis`/`source_map`/T0 就绪 → 可真接 B1、B6 |
| A8 词库 | A4 A7 | 无 | **NOTIFY B**：确认版 keywords → 可真接 B1 |
| A9 设置/主攻AI | A1 A5 | **WAIT_FOR B6**（真实验证「改引擎→监测切换」时） | 改 `target_engines` 后 **NOTIFY B** 复测监测 |

### B 任务依赖

| 任务 | 己方前置 | 跨人依赖 | 完成后 NOTIFY |
|------|----------|----------|---------------|
| B0 UI mock | — | **WAIT_FOR A**：至少 A 提供 §2.3 fixture（可先手写同结构）· `MOCK_OK` | — |
| B1 方案包生成 | B0 | **WAIT_FOR A7+A8**（真接）· W1–W3 可用 fixture · `MOCK_OK`；另需 **A3** `chat()`、**A0** `channel_defaults`/`persona_hint` | — |
| B2 confirm | B1 | 无（数据已在 B1） | — |
| B3 内容工厂 | B2 | **WAIT_FOR A2**（真 `kb_facts`）· **WAIT_FOR A3**（`chat()`）· fixture 可先 · `MOCK_OK` | — |
| B4 检测+闸门 | B3 | **WAIT_FOR A0**（`forbidden_words`/`compliance`） | **NOTIFY A**：闸门后可联调发布路径 |
| B5 发布 | B4 | **WAIT_FOR A5**（托管页骨架/域名约定，真发托管页时） | **NOTIFY A**：可对发布后链路做抽检 |
| B6 监测 T1+Δ | B5 | **WAIT_FOR A7**（T0 `baseline=true`）· **WAIT_FOR A9**（验 AC-13 主攻 AI 联动时） | — |
| B7 效果舱 | B6 | **WAIT_FOR A7**（T0 指标） | — |
| B8 下游前端 | B1–B7 | 真接时分别继承上表 WAIT_FOR；mock 阶段 `MOCK_OK` | — |

### 联调 GATE（双方都绿才过）

| GATE | 需要 A | 需要 B | Agent 提示 |
|------|--------|--------|------------|
| **G1** 信封+JWT | A1 完成 | B 任意受保护 API 能 401/200 | 缺 A1 → 提示 A |
| **G2** 诊断→方案包 | A7+A8+fixture 换真 | B1 读真 API 五区正确 | 缺 A → 提示 A；缺 B → 提示 B |
| **G3** 闸门→发布 | A0 禁词可用；A5 托管页可挂 | B4+B5 | 按缺项提示 |
| **G4** T0/T1 Δ | A7 T0 | B5+B6 T1 | 缺 T0 → 提示 A；缺 T1 → 提示 B |
| **G5** AC-01 全链路 | A 过线 §2.4 | B 过线 §3.3 | 任一侧未过 → 提示该侧 |

---

## 2. 开发者 A · 上游任务

### 2.1 任务清单（含依赖列）

| # | 任务 | 依赖 | 对应实施清单 | 验收标准 |
|---|------|------|:------------:|----------|
| A0 | IndustryPack 基类 + `beauty_local` 规则簿瘦身（9 项） | 依赖: 无 · **NOTIFY B** | 0.1 · 0.2 | `get_industry_pack("beauty_local")` 可取禁词/合规/渠道/few-shot |
| A1 | 注册 / 登录 / JWT / RBAC / 租户隔离 | 依赖: 无 · **NOTIFY B** | — | 跨 enterprise API → `403`（AC-14） |
| A2 | KB CRUD（Fact / FAQ / Signal） | 己方 A1 · **NOTIFY B** | — | `kb_facts.id` 可被 B 的 `fact_refs` 引用（AC-02 上游） |
| A3 | LLM Gateway × 4 EngineAdapter | 依赖: 无 · **NOTIFY B** | 0.4 | 统一 `chat()`；豆包/DeepSeek/Kimi/文心通 |
| A4 | Faiss per-tenant | 己方 A1 · **NOTIFY B** | 0.3 | 按 `enterprise_id` 隔离 add/search |
| A5 | 开店向导 API：建库 + Schema + llms.txt + 激活行业包 | 己方 A0 A1 A2 | 1.1 · 1.2 | `POST /onboarding/run` → `{ task_id }` |
| A6 | onboarding SSE 进度 | 己方 A5 | 0.5 · 1.3 | `progress_pct` 到 100 + `next_route` |
| A7 | 诊断 5 项 + 写 T0 | 己方 A3 A5 A6 · **NOTIFY B**（解锁 B1 真接、B6） | 1.4–1.8 | `GET /diagnosis/{id}` 字段齐全；T0 入库（AC-04 · AC-12 上游） |
| A8 | 四源汇聚词库 + CRUD + generate | 己方 A4 A7 · **NOTIFY B**（解锁 B1 真接） | 1.9 · 1.10 | 四层 + 来源标注 + 租户隔离（AC-05） |
| A9 | 前端：登录 / 入驻 / KB / 设置（含改 `target_engines`） | 己方 A1 A5 · **WAIT_FOR B6**（仅当验收 AC-13 端到端时） | 1.1 · 4.1 | 入驻完成可跳转 `/strategy-pack`；改引擎后监测跟随 |

### 2.1.1 A 各任务 · Agent 提示对方话术

#### A0 完成后

```text
【NOTIFY · 请通知开发者 B】
A0 IndustryPack 已完成。
你可在 B4 检测中调用：forbidden_words / banned_patterns / compliance_checklist。
你可在 B1 使用：channel_defaults / persona_hint / scenario_few_shot。
路径：agents/industry/packs/beauty_local/
```

#### A1 / A2 / A3 完成后（合并可发）

```text
【NOTIFY · 请通知开发者 B】
底座已就绪：JWT(A1) · KB CRUD(A2) · LLM Gateway chat()(A3)。
你可开始/继续：B1（调 chat）· B3（kb_fetch + fact_refs 指向真实 kb_facts.id）。
请确认请求头带 Authorization: Bearer <JWT>。
```

#### A7 完成后（关键）

```text
【NOTIFY · 请通知开发者 B · 解锁 B1 真接 / B6 Δ】
A7 诊断已完成。
请消费：
  - GET /api/v1/user/diagnosis/{id}（含 source_map.rankings / gaps）
  - T0：monitor_results 或等价基线，baseline=true
请将 B1 从 fixture 切换为真实 diagnosis；B6 可用 T0 算 Δ。
契约：G-L3-API契约.md §4 · §9
```

#### A8 完成后（关键）

```text
【NOTIFY · 请通知开发者 B · 解锁 B1 词库区真接】
A8 词库已完成。
请消费：GET /api/v1/user/keywords（四层 + source + lbs_tags）。
B1 方案包 E 区与 scenario 候选请改读真实 keywords，停用 mock。
```

#### A9 做到「验收主攻 AI 联动」时

```text
【WAIT_FOR · 请通知开发者 B】
我方正在验收 A9 / AC-13：修改 target_engines 后监测应切换。
需要对方先完成：B6（Core/Probe 监测已按 enterprise.target_engines 选 EngineAdapter）。
请 B 确认：PUT /enterprise { target_engines } 之后，下次 monitor_run 引擎列表已变。
在 B6 完成前：A9 设置页 UI 可先做，端到端联动验收暂停。
```

---

### 2.2 A 的关键输入 / 输出

#### A5 入驻 · `POST /api/v1/user/onboarding/run`

**输入：**

```json
{
  "target_engines": ["doubao", "deepseek"],
  "industry": "beauty_local",
  "brand": { "name": "倾城美业", "differentiator": "透明价格 + 1v1" },
  "stores": [
    {
      "name": "XX路店",
      "address": "静安区XX路88号",
      "lat": 31.23,
      "lng": 121.45,
      "phone": "021-12345678",
      "hours": "10:00-22:00"
    }
  ],
  "services": [
    {
      "name": "敏感肌修护",
      "price_range": "298-498元",
      "duration": "60分钟",
      "target_group": "敏感肌人群"
    }
  ],
  "target_customers": ["敏感肌人群", "白领女性"],
  "competitors": [{ "name": "XX美容连锁", "url": "https://..." }],
  "differentiator": "透明价格 + 成分公开 + 1v1客制化",
  "raw_inputs": "客户常问：敏感肌能做吗？会不会越做越敏感？..."
}
```

**输出：**

```json
{ "task_id": "a1b2c3d4", "status": "pending" }
```

**副作用：** 写 Brand / Store / Service / KBFact / KBSignal；激活 IndustryPack；生成托管页 + Schema + llms.txt。

#### A6 进度 · SSE `GET /api/v1/user/onboarding/status/{task_id}`

**输出（流式）：**

```json
{ "step": "DIAGNOSE", "progress_pct": 25, "progress_message": "DIAGNOSE done" }
```

完成时：

```json
{ "progress_pct": 100, "next_route": "/strategy-pack?draft=1" }
```

> **跨人提示：** SSE 完成后前端会跳转 B 的 `/strategy-pack`。若 B0/B1 页面未就绪：  
> Agent 提示 B：「A6 已可跳转方案包，请优先保证 B0/B1 路由可打开（可先 mock）。」

#### A7 诊断 · `GET /api/v1/user/diagnosis/{id}`

**输出（节选）：**

```json
{
  "id": 1,
  "engine_code": "doubao",
  "probe_prompts": ["静安寺附近皮肤管理推荐", "敏感肌能不能做皮肤管理"],
  "brand_mention_rate": 0.05,
  "hallucination_rate": 0.0,
  "competitor_occupancy": { "XX美容连锁": 0.4 },
  "source_map": {
    "rankings": [
      { "domain": "dianping.com", "count": 12, "weight": 0.35 },
      { "domain": "zhihu.com", "count": 8, "weight": 0.24 }
    ],
    "gaps": ["今日头条", "小红书"]
  },
  "track": "blank",
  "competitor_analysis": [
    {
      "name": "XX美容连锁",
      "type": "chain",
      "strengths": ["品牌知名度"],
      "weaknesses": ["客制化差"],
      "differentiation": "本地化定制 + 1v1"
    }
  ]
}
```

同时写入 `source_diagnoses` / T0 监测基线（`baseline=true`）。

#### A8 词库标准形状

```json
{
  "id": 1,
  "keyword": "静安寺皮肤管理推荐",
  "layer": "选型层",
  "source": "LLM生成",
  "lbs_tags": ["静安区", "静安寺商圈"]
}
```

`layer` 枚举：`认知层` | `选型层` | `痛点层` | `场景层`  
`source` 枚举：`RawInputs` | `探针反推` | `SEO API` | `LLM生成` | `手动`

### 2.3 A → B 硬交接包（缺一不可）

B 可在 W1 用 fixture mock；**GATE G2（约 W4）起必须替换为真实数据**。

```json
{
  "enterprise": {
    "id": 1,
    "industry_pack": "beauty_local",
    "target_engines": ["doubao", "deepseek"]
  },
  "diagnosis": {
    "source_map": {
      "rankings": [{ "domain": "dianping.com", "count": 12, "weight": 0.35 }],
      "gaps": ["今日头条"]
    },
    "competitor_analysis": [],
    "probe_prompts": [],
    "brand_mention_rate": 0.05
  },
  "keywords": [
    {
      "keyword": "静安寺皮肤管理推荐",
      "layer": "选型层",
      "source": "LLM生成",
      "lbs_tags": ["静安区"]
    }
  ],
  "kb_facts": [
    {
      "id": 1,
      "title": "补水管理项目价格",
      "content": "298-498 元/次",
      "category": "price"
    }
  ],
  "t0_ready": true
}
```

**建议路径：** `backend/tests/fixtures/handoff_a_to_b/`（`enterprise.json` · `diagnosis.json` · `keywords.json` · `kb_facts.json`），由 **A 维护**。

**若 B 开工时 fixture 不存在：**

```text
【WAIT_FOR · 请通知开发者 A】
B0/B1 需要 handoff fixture，路径 backend/tests/fixtures/handoff_a_to_b/。
请 A 先提交与本文 §2.3 同结构的 JSON（可先手写假数据）。
在 fixture 就绪前：B 可在前端内联同结构 mock，但须标注 TODO(WAIT_FOR: A-fixture)。
```

### 2.4 A 过线标准

入驻选主攻 AI → SSE 跑完 → GEO 健康报告可读 → 四层词库可编辑 → T0 入库 → 设置页可改 `target_engines`。

---

## 3. 开发者 B · 下游任务

### 3.1 任务清单（含依赖列）

| # | 任务 | 依赖 | 对应实施清单 | 验收标准 |
|---|------|------|:------------:|----------|
| B0 | 用 fixture mock 方案包 / 草稿页骨架 | **WAIT_FOR A-fixture** · `MOCK_OK` | — | 五区 UI 可渲染 |
| B1 | persona + scenario + 权重 0.6/0.4 | 己方 B0 · **WAIT_FOR A7+A8**（真接）· **WAIT_FOR A3/A0** · `MOCK_OK` | 2.1–2.3 | `GET /strategy-pack/draft` 五区齐全（AC-06 · AC-07 · AC-08） |
| B2 | `POST /strategy-pack/confirm` | 己方 B1 | 2.4 · 2.5 | 落 scenarios + strategy_pack；触发内容 Job |
| B3 | 内容工厂：固定链 + 7 段式 + RAG 切片 | 己方 B2 · **WAIT_FOR A2+A3** · `MOCK_OK` | 2.6–2.8 | drafts 含 `fact_refs` + `rag_slices`（AC-09） |
| B4 | 5 项机审 + 人闸门 + `approval_log` | 己方 B3 · **WAIT_FOR A0**（禁词/合规） | 2.9–2.14 | `bulk-approve`；策略+草稿一次确认（AC-10 · AC-11） |
| B5 | 发布：托管页 AUTO + 小红书 SEMI | 己方 B4 · **WAIT_FOR A5**（真发托管页时） | 3.1 · 3.3 · 3.5 | `publish_tasks` 带 `content_asset_id` |
| B6 | Core/Probe + T1 + T0/T1 Δ + Engine 联动 | 己方 B5 · **WAIT_FOR A7**（T0）· **WAIT_FOR A9**（验 AC-13 时） | 3.6–3.9 · 3.12 | Δ 可展示；改主攻 AI 后监测跟随（AC-12 · AC-13） |
| B7 | 效果舱 Dashboard | 己方 B6 · **WAIT_FOR A7**（T0 KPI） | 3.14 | `GET /outcomes/dashboard` |
| B8 | 前端：方案包 / 草稿 / 发布 / 监测 / 效果舱 | 随 B1–B7；真接继承各 WAIT_FOR · `MOCK_OK` | — | MVP-A 后半段可点通 |

### 3.1.1 B 各任务 · Agent 提示对方话术

#### B0 / B1 真接前（缺诊断或词库）

```text
【WAIT_FOR · 请通知开发者 A】
我方正在实现：B1 方案包生成（或 B0→B1 真接切换）。
被阻塞原因：需要 A7 诊断（source_map）+ A8 确认版 keywords。
需要对方交付：
  - GET /diagnosis/{id} 含 source_map.rankings / gaps
  - GET /keywords 四层列表
  - 或更新 backend/tests/fixtures/handoff_a_to_b/
验收看：B1 五区能用真实数据算出 mixed_weight = 0.6*model + 0.4*probe。
在对方交付前：继续使用 §2.3 fixture（MOCK_OK），代码留 TODO(WAIT_FOR: A7+A8)。
```

#### B1 缺 LLM Gateway

```text
【WAIT_FOR · 请通知开发者 A】
我方正在实现：B1 persona/scenario LLM 生成。
被阻塞原因：需要 A3 LLM Gateway 的 chat() 可用（含至少 1 个 engine）。
请确认：backend app.core.llm.gateway 可对 doubao/deepseek 等返回 content。
在对方交付前：可用固定 JSON stub 生成五区，禁止在 B 目录内自建第二套 LLM 客户端。
```

#### B3 缺 KB / Gateway

```text
【WAIT_FOR · 请通知开发者 A】
我方正在实现：B3 内容工厂（kb_fetch → LLM → 输出）。
被阻塞原因：需要 A2 KB Fact 可查；需要 A3 chat()。
需要对方交付：
  - GET /kb/facts 返回可用 id（供 fact_refs）
  - gateway.chat() 稳定
在对方交付前：fixture 中的 kb_facts 可注入本地；TODO(WAIT_FOR: A2+A3)。
```

#### B4 缺行业包禁词

```text
【WAIT_FOR · 请通知开发者 A】
我方正在实现：B4 禁词拦截 / 合规机审。
被阻塞原因：需要 A0 IndustryPack.forbidden_words() / banned_patterns() / compliance_checklist()。
请确认：get_industry_pack(enterprise.industry_pack) 可加载 beauty_local。
禁止在 content_service 内硬编码生美禁词副本（以免与规则簿漂移）。
```

#### B5 真发托管页时

```text
【WAIT_FOR · 请通知开发者 A】
我方正在实现：B5 托管页 AUTO 发布。
被阻塞原因：需要 A5 入驻时生成的托管页骨架 / Schema / 存储约定（OSS 路径或本地 uploads 规范）。
需要对方交付：托管页 URL 规则 + 已存在的页面写入点说明。
SEMI 导出包不阻塞，可先做；AUTO 真发暂停至 A5 约定清晰。
```

#### B6 / B7 缺 T0

```text
【WAIT_FOR · 请通知开发者 A】
我方正在实现：B6 T0/T1 对比（或 B7 效果舱 KPI）。
被阻塞原因：需要 A7 写入 T0（monitor_results.baseline=true 或文档约定的等价表字段）。
需要对方交付：
  - 与 T1 同构的 prompt 列表基线
  - brand_mentioned / hallucination 等字段
验收看：dashboard 能算出 delta_mention。
在对方交付前：可用 fixture 假 T0 出 UI，联调 GATE G4 不得标绿。
```

#### B6 验 AC-13 时缺设置页联动

```text
【WAIT_FOR · 请通知开发者 A】
我方正在验收：B6 / AC-13 EngineAdapter 跟随 target_engines。
被阻塞原因：需要 A9 设置页（或 PUT /enterprise）能改 target_engines 并落库。
请 A 提供可操作的改引擎入口后，我方复测 monitor 引擎列表。
```

#### B4/B5 完成后

```text
【NOTIFY · 请通知开发者 A】
B4 人闸门 + B5 发布主路径已通（或达联调标准）。
可进入 GATE G3：请抽检托管页 URL / Schema；准备 GATE G4 的 T0 对齐。
```

---

### 3.2 B 的关键输入 / 输出

#### B1 方案包草案 · `GET /api/v1/user/strategy-pack/draft`

**依赖输入：** A 交接包中的 `diagnosis.source_map` + 确认版 `keywords` + `kb_facts`（真接时 **WAIT_FOR A7+A8+A2**）。

**输出五区：**

```json
{
  "id": 1,
  "persona": {
    "buyer_personas": [
      {
        "role": "静安寺白领女性",
        "age_range": [25, 35],
        "pain_tags": ["敏感肌", "怕推销"],
        "decision_factors": ["口碑", "资质", "距离"],
        "trust_triggers": ["VISIA报告", "评价带图"]
      }
    ],
    "content_layout_plan": [
      {
        "persona": "敏感肌白领",
        "content_type": "FAQ+场景推荐",
        "channel": "小红书+知乎",
        "cta": "预约小程序"
      }
    ]
  },
  "competitors": {
    "profiles": [],
    "differentiation_brief": "...",
    "content_gaps": ["缺少敏感肌修护FAQ"]
  },
  "scenarios": {
    "candidates": [
      {
        "id": "c1",
        "user_query": "敏感肌能不能做皮肤管理",
        "intent": "项目咨询",
        "channel": "hosted",
        "skill": "faq"
      }
    ],
    "recommended_count": 3,
    "max": 5
  },
  "channels": [
    {
      "name": "AI托管页",
      "model_weight": 0.4,
      "probe_weight": 0.1,
      "mixed_weight": 0.28,
      "scenario_count": 1
    }
  ],
  "keywords": {
    "layers": {
      "选型层": [],
      "场景层": [],
      "痛点层": [],
      "认知层": []
    }
  },
  "kb_freshness": { "warning": false, "updated_at": "2026-07-16T10:00:00Z" }
}
```

**权重公式（实现约束）：**

```
mixed_weight = model_weight × 0.6 + probe_weight × 0.4
```

#### B2 确认 · `POST /api/v1/user/strategy-pack/confirm`

**输入：**

```json
{
  "selected_scenarios": ["c1", "c2"],
  "channel_overrides": { "xiaohongshu": 1 },
  "persona_confirmed": true,
  "competitor_confirmed": true
}
```

**输出：**

```json
{
  "strategy_pack_id": 1,
  "status": "confirmed",
  "next_route": "/content/drafts"
}
```

#### B3–B4 草稿标准形状 · `GET /api/v1/user/content/drafts`

```json
{
  "id": 1,
  "scenario_id": 1,
  "channel": "hosted",
  "skill": "faq",
  "title": "敏感肌能不能做皮肤管理？",
  "body": "可以。敏感肌先做 VISIA 检测...",
  "fact_refs": [1, 5, 8],
  "rag_slices": [
    {
      "title": "...",
      "summary": "...",
      "keywords": ["敏感肌", "VISIA"],
      "body": "...",
      "chars": 420
    }
  ],
  "machine_review": {
    "fact_verify": true,
    "forbidden_words": false,
    "cross_validation": true,
    "entity_consistency": true,
    "rag_readability": true
  },
  "status": "ready"
}
```

**content_unit：** `1 scenario × 1 channel × 1 skill`  
**fact_refs：** 必须是 `kb_facts.id[]`（来自 A · **WAIT_FOR A2**）

| API | 输入 | 输出 |
|-----|------|------|
| `POST .../bulk-approve` | `{ "ids": [1, 2, 3] }` | `{ "approved": 3, "failed": [], "next_route": "/publish/tasks" }` + 写 `approval_logs` |
| `POST .../{id}/reject` | `{ "reason": "价格需更新" }` | `{ "id": 1, "status": "draft" }` |

人闸门 `approval_logs.target_type`：`strategy_pack+content`

#### B5 发布任务

```json
{
  "id": 1,
  "content_asset_id": 1,
  "channel": "hosted",
  "mode": "AUTO",
  "status": "pending",
  "export_package": null
}
```

SEMI 时 `export_package` 必填：

```json
{
  "title": "...",
  "body": "...",
  "tags": ["皮肤管理", "敏感肌"],
  "cover_hint": "使用 VISIA 检测过程图",
  "steps": ["打开小红书APP", "粘贴文案", "上传图片", "发布"]
}
```

#### B6 监测结果（T0/T1 同构）

```json
{
  "engine_code": "doubao",
  "prompt": "静安寺皮肤管理推荐",
  "brand_mentioned": false,
  "rank": null,
  "hallucination": false,
  "citations": ["dianping.com/..."],
  "baseline": true
}
```

- `baseline: true` → T0（由 **A** 在 A7 写入）· B 侧 **WAIT_FOR A7**  
- `baseline: false` → T1（由 **B** 在发布 24h 后写入）

#### B7 效果舱 · `GET /api/v1/user/outcomes/dashboard`

```json
{
  "kpi": {
    "mention_rate_t0": 0.05,
    "mention_rate_t1": 0.22,
    "delta_mention": 0.17,
    "hallucination_rate": 0.0
  },
  "funnel": {
    "exposure": { "ok": true },
    "trust": { "ok": true },
    "leads": { "form_submits": 3 },
    "conversion": { "manual_cost": null, "manual_revenue": null }
  },
  "geo_efficiency": 0.42
}
```

### 3.3 B 过线标准

勾选 ≤5 个 scenario → 草稿过 5 项机审 → 策略+草稿一次人闸门 → 托管页 AUTO + 小红书 SEMI → 效果舱可见 T0/T1 Δ。

---

## 4. 交接关系

```
开发者 A                              开发者 B
────────                              ────────
底座(JWT/KB/Pack/LLM/Faiss)
   │
入驻 → 诊断 → 词库 → T0
   │
   ├──── fixture / 真实 API ─────────► 方案包（吃 source_map + keywords）
   │         WAIT_FOR A7+A8                │
   │                                   内容工厂 → 检测 → 人闸门
   │                                   WAIT_FOR A2+A3 / A0
   │                                       │
   │                                   发布 AUTO/SEMI
   │                                   WAIT_FOR A5(真发)
   │                                       │
   └──── T0 (baseline=true) ─────────► 监测 T1 → Δ → 效果舱
              WAIT_FOR A7
```

| 交接节点 | 提供者 | 消费者 | 阻塞任务 | 格式依据 |
|----------|--------|--------|----------|----------|
| JWT + enterprise（含 `target_engines`） | A | B | B 任意真 API · **WAIT_FOR A1** | API §1–2 |
| `diagnosis` + `source_map` | A | B 算渠道权重 | **B1 真接 WAIT_FOR A7** | API §4 |
| 确认版 `keywords` | A | B 方案包 E 区 / scenario | **B1 真接 WAIT_FOR A8** | API §5 |
| `kb_facts.id` | A | B `fact_refs` / fact_verify | **B3 WAIT_FOR A2** | API §3 |
| IndustryPack 禁词/合规 | A | B 机审 | **B4 WAIT_FOR A0** | IndustryPack |
| LLM `chat()` | A | B 画像/正文 | **B1/B3 WAIT_FOR A3** | gateway |
| 托管页写入约定 | A | B AUTO 发布 | **B5 WAIT_FOR A5** | 入驻产出 |
| T0 `monitor_results` | A | B 算 Δ | **B6/B7 WAIT_FOR A7** | API §9 · `baseline=true` |
| ready `content_assets` | B | B 发布 | B5 己方 B4 | API §7–8 |
| 监测跟随 `target_engines` | A 改库 + B 读库 | 双方验 AC-13 | **A9 WAIT_FOR B6** 且 **B6 WAIT_FOR A9** | Enterprise PUT |

---

## 5. 共用枚举与约定

| 项 | 取值 |
|----|------|
| 引擎 code | `doubao` \| `deepseek` \| `kimi` \| `wenxin` |
| 渠道 | `hosted` \| `xiaohongshu` \| `zhihu` \| `dianping` \| `sohu` \| `toutiao` \| `wechat` |
| 发布模式 | `AUTO` \| `SEMI` \| `GUIDED` |
| 草稿状态 | `draft` \| `ready` \| `published` \| `rejected` |
| 分页 | `?page=1&page_size=20` → `{ items, total, page, page_size }` |
| 异步 | `202` + `{ task_id, status }`；进度用 SSE |

**Agent 红线（两人共同遵守）：**

- 禁止 Agent `write_fact` / `auto_confirm` / 直接 `publish`
- 正文 Skill **不用 ReAct**：固定链 `kb_fetch → LLM → fact_verify`
- 跨租户访问一律 `403`
- **禁止**为绕过 `WAIT_FOR` 而改对方目录或复制对方模块实现

---

## 6. 双人 8 周排期（含闸门）

| 周 | 开发者 A | 开发者 B | GATE / Agent 动作 |
|:--:|----------|----------|-------------------|
| W1 | A0–A4 底座；§2.3 fixture 定稿 | B0 mock 五区/草稿 | **G1**：缺 JWT → 提示 A |
| W2 | A5–A6 入驻 + SSE；入驻前端 | B1–B2 方案包（吃 fixture） | B 真接前勿催；缺 fixture → 提示 A |
| W3 | A7 诊断主路径；健康报告页 | B3 内容工厂 + RAG | A7 完成 → **NOTIFY B**；B 缺 A2/A3 → 提示 A |
| W4 | A8 词库；真实 diagnosis 替换 mock | B4 检测 + 人闸门 | **G2**：缺 A7/A8 → 提示 A；缺 B1 → 提示 B |
| W5 | A9 设置 / 主攻 AI；T0 写入规范 | B5 发布 AUTO + SEMI | B5 真发缺托管页约定 → 提示 A |
| W6 | 联调修补；Pack 禁词供 B | B6 监测 T1 + Engine 联动 | **G3**；**G4**：缺 T0 → 提示 A；缺 T1 → 提示 B |
| W7 | 前半路径稳定 | B7–B8 效果舱 + 舱3 前端 | AC-13 互等：A9↔B6 按 WAIT_FOR 互提示 |
| W8 | 端到端 AC-01 前半 | 端到端 AC-01 后半 | **G5**：任一侧未过线 → 提示该侧 |

合计对齐 [G-L3-实施清单.md](G-L3-实施清单.md)：**8–10 周 MVP-A**。

---

## 7. 协作规则

1. **只改自己轨目录**；跨轨需求提「契约变更 PR」，必须同时改：`G-L3-API契约.md` + 对应 `schemas/` + fixture。
2. **A 维护** `handoff_a_to_b` fixture；B 的单测默认吃 fixture，联调日再切真实 API。
3. **固定联调日**：W4（G2 诊断→方案包）、W6（G3/G4 闸门→发布→Δ）、W8（G5 全链路）。
4. **冲突高发区 Owner：**
   - `core/llm/` → **A**
   - `agents/industry/`（禁词/合规）→ **A** 配，**B** 只读调用
   - `content_*` / `approval_logs` / `publish_*` → **B**
5. **每日 standup / Agent 汇报**须包含：当前任务号、是否命中 `WAIT_FOR`、已向谁发出提示话术。
6. **代码内标记**：跨人未就绪处写 `TODO(WAIT_FOR: A7)` 或 `TODO(WAIT_FOR: B6)`，便于 Agent/人检索。

---

## 8. 合并验收（AC-01）

两人串一次生美 1 店最小路径：

```
入驻(选主攻AI) → 诊断(探针LLM·5项) → 词库(四源)
→ 方案包(persona+scenario·勾选2个) → 内容(RAG切片) → 检测(5项)
→ 人闸门(策略+草稿合并) → 发布(托管页AUTO+小红书SEMI)
→ 监控(24h T0/T1) → 效果舱(四层漏斗)
```

| 角色 | 个人过线 | 共同过线 |
|------|----------|----------|
| A | 舱1 + T0 + 词库可编辑 | AC-01 · AC-04 · AC-05 · AC-14 · AC-15 |
| B | 舱2+舱3 可发布可看 Δ | AC-01 · AC-02 · AC-03 · AC-06～AC-13 |

完整 AC 表见 [G-L1-需求规格说明书.md](G-L1-需求规格说明书.md) §9 · [G-L3-实施清单.md](G-L3-实施清单.md) §7。

**Agent 在宣称 AC-01 通过前**：必须逐项确认 G1–G5；若某 GATE 依赖未满足，输出对应 `WAIT_FOR` 提示，**不得**标为通过。

---

## 9. 延后项（两人都不做 · MVP）

| 延后项 | 版本 |
|--------|------|
| 本地账号浏览器自动化发布 | V1.1 |
| ConsultLog 完整归因 | V1.1 |
| 餐饮等新品类行业包 | V1.2+ |
| 微信小程序 / B2B | V2 |

---

## 10. Agent 检查清单（实现任一步前勾选）

```text
[ ] 我已读 G-L3-开发进度.md：当前任务行状态与对方前置是否 done
[ ] 我已确认当前任务号（Ax 或 Bx）
[ ] 我已查 §1.2 依赖总表
[ ] 若有 WAIT_FOR：我已向用户展示「提示对方」话术，且未改对方目录
[ ] 若有 MOCK_OK：我仅用 fixture/stub，并写了 TODO(WAIT_FOR: …)
[ ] 若任务完成且有 NOTIFY：我已提示对方可开始的任务号，并更新开发进度表
[ ] 若宣称联调/AC 通过：我已核对对应 GATE G1–G5，并更新开发进度表
[ ] 进度变更已按 progress: … 格式准备 git commit（见开发进度表 §0 / §6）
```

---

*G-L3-双人任务拆分 v1.2 · 关联开发进度表 · WAIT_FOR/NOTIFY/GATE · 对齐 PRD/需求规格 v2.1 + API 契约 v2.1*
