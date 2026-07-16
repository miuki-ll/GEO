# GEO 开发者 B · 下游任务手册

> **版本**：v1.1 | **日期**：2026-07-16  
> **你是谁**：开发者 B（下游）— 让方案能确认、写出稿、发出去、看出效果  
> **完整双人约定**：[G-L3-双人任务拆分.md](G-L3-双人任务拆分.md)  
> **进度同步（git）**：[G-L3-开发进度.md](G-L3-开发进度.md) — 只改其中「开发者 B」相关行  
> **API 契约**：[G-L3-API契约.md](G-L3-API契约.md) · **实施清单**：[G-L3-实施清单.md](G-L3-实施清单.md)  
> **v1.1**：新增 §3.1–§3.3（强制顺序 · 可先行/须等 A · 仓库快照）

---

## 0. 一句话范围

| 你负责 | 你不负责（开发者 A） |
|--------|----------------------|
| 舱2 定方案 + 舱3 出结果 | 舱1 懂我 + 平台底座 |
| 管道步骤 4→8：策略 · 内容 · 检测 · 人闸门 · 发布 · 监控 · 效果舱 | 入驻 · 诊断 · 词库 · JWT/KB/IndustryPack/LLM Gateway |
| FR-SP / FR-CF / FR-CK / FR-GT / FR-PB / FR-MN / FR-CV | FR-ON / FR-DG / FR-KW |

**对外用户路径（你交付的后半段）：**

```
方案包五区 → 勾选 scenario → 生成草稿 → 机审 → 人闸门
→ 发布(AUTO/SEMI) → 监测 T1 → 效果舱(T0/T1 Δ + 四层漏斗)
```

---

## 1. 代码目录（只改这些）

| 层 | 路径 |
|----|------|
| API | `backend/app/api/v1/user/strategy_pack.py` · `content.py` · `publish.py` · `monitoring.py` · `outcomes.py` |
| Service | `strategy_service.py` · `scenario_service.py` · `content_service.py` · `publish_service.py` · `monitor_service.py` · `dashboard_service.py` |
| 内容链 | SkillRuntime / 检测链（kb_fetch→LLM→fact_verify 固定链，**不用 ReAct**） |
| 前端 | `views/strategy/` · `content/` · `publish/` · `monitor/` · `outcomes/` · `api/strategy.ts`（及下游 API 封装） |
| 表 | `scenarios` · `strategy_pack_*` · `content_*` · `approval_logs` · `publish_tasks` · `monitor_*` · `outcome_snapshots` · `hosted_page_events` |

**禁止改：** `core/llm/` · `agents/industry/` · `graphs/onboarding/` · 入驻/诊断/词库/登录相关前端（属 A）。  
**只读调用：** IndustryPack（禁词等）· `gateway.chat()`（A 维护）。

**共建（PR 双方 review）：** `G-L3-API契约.md` · 跨域 `models/` / `schemas/` · Alembic。

---

## 2. 依赖协议（Agent 必读）

| 标记 | 你怎么做 |
|------|----------|
| `WAIT_FOR: Ax` | **不要**改 A 的目录；向用户展示 §5 话术通知 A；有 `MOCK_OK` 可用 fixture 继续 |
| `MOCK_OK` | 用 `backend/tests/fixtures/handoff_a_to_b/` 或内联同结构 mock，写 `TODO(WAIT_FOR: …)` |
| `NOTIFY: A` | 完成后提示 A 可抽检 / 联调 |
| 进度 | 改状态后更新 [G-L3-开发进度.md](G-L3-开发进度.md) 并 `git commit -m "progress: B…"` + `push` |

统一信封：`{ "code": 0, "data": {}, "msg": "ok" }` · Header：`Authorization: Bearer <JWT>`。

---

## 3. 任务总表（B0–B8）

| # | 任务 | 己方前置 | 跨人依赖 | 实施清单 | 验收 |
|---|------|----------|----------|:--------:|------|
| **B0** | 方案包/草稿页骨架（fixture mock） | — | **WAIT_FOR A-fixture** · `MOCK_OK` | — | 五区 UI 可渲染 |
| **B1** | persona + scenario + 权重 0.6/0.4 | B0 | **WAIT_FOR A7+A8**（真接）· **A3/A0** · `MOCK_OK` | 2.1–2.3 | `GET /strategy-pack/draft` 五区（AC-06/07/08） |
| **B2** | `POST /strategy-pack/confirm` | B1 | 无 | 2.4–2.5 | 落 scenarios + strategy_pack；触发内容 Job |
| **B3** | 内容工厂：固定链 + 7 段式 + RAG 切片 | B2 | **WAIT_FOR A2+A3** · `MOCK_OK` | 2.6–2.8 | drafts 含 `fact_refs` + `rag_slices`（AC-09） |
| **B4** | 5 项机审 + 人闸门 + `approval_log` | B3 | **WAIT_FOR A0**（禁词/合规） | 2.9–2.14 | `bulk-approve`（AC-10/11）· **NOTIFY A** |
| **B5** | 托管页 AUTO + 小红书 SEMI | B4 | **WAIT_FOR A5**（真发托管页时） | 3.1/3.3/3.5 | `publish_tasks` + `content_asset_id` · **NOTIFY A** |
| **B6** | Core/Probe + T1 + T0/T1 Δ + Engine 联动 | B5 | **WAIT_FOR A7**（T0）· 验 AC-13 时 **WAIT_FOR A9** | 3.6–3.9/3.12 | Δ 可展示（AC-12/13） |
| **B7** | 效果舱 Dashboard | B6 | **WAIT_FOR A7**（T0 KPI） | 3.14 | `GET /outcomes/dashboard` |
| **B8** | 前端：方案包/草稿/发布/监测/效果舱 | 随 B1–B7 | 真接继承上表 · `MOCK_OK` | — | MVP-A 后半段可点通 |

### 推荐开工顺序（周历）

```
W1–W2: B0 → B1(fixture) → B2
W3:    B3(fixture KB)
W4:    B4（需 A0）→ G2 真接（需 A7+A8）
W5:    B5（SEMI 可先；AUTO 需 A5）
W6:    B6（需 A7 T0）→ G3/G4
W7:    B7 + B8 收尾
W8:    G5 AC-01 与 A 串全链路
```

### 3.1 开发顺序（强制依赖）

**己方严格串行：** `B0 → B1 → B2 → B3 → B4 → B5 → B6 → B7`；`B8` 可与后端并行，真接跟随各步。

| 顺序 | 任务 | 本周建议 | 可先做什么 | 做到哪必须停 / 换真 |
|:----:|------|----------|------------|---------------------|
| 1 | **B0** | W1 | 五区/草稿页骨架；无官方 fixture 时可**手写同结构 mock**（标 `TODO(WAIT_FOR: A-fixture)`） | 官方交接目录未提交前不算「交接完成」 |
| 2 | **B1** | W1–W2 | 用 fixture/静态五区实现 draft API + UI；权重公式可先写死算 | **真接**须 A7+A8；LLM 画像/scenario 须 A3；渠道默认/persona_hint 须 A0 |
| 3 | **B2** | W2 | confirm 落库 + 触发内容 Job（**己方无跨人硬依赖**） | — |
| 4 | **B3** | W3 | 固定链骨架、7 段式、RAG 切片结构；KB 用 fixture id | **真 fact_refs / chat 生成**须 A2+A3 |
| 5 | **B4** | W4 | 闸门 UI + approval_log；可先做部分机审 | **禁词走 IndustryPack**须 A0（勿长期硬编码副本） |
| 6 | **B5** | W5 | **SEMI 导出包可先做完** | **托管页 AUTO 真发**须 A5 |
| 7 | **B6** | W6 | Core/Probe 配置、T1 写入、模拟结果 | **T0/Δ 真对比**须 A7；**AC-13**须 A9 |
| 8 | **B7** | W7 | Dashboard 壳 + 漏斗 UI | **真 T0 KPI**须 A7 |
| 9 | **B8** | 贯穿 W1–W7 | 各页 API 封装与接线（可与上并行） | 真接继承上表各 WAIT_FOR |

联调闸门：`G1(JWT)` → `G2(诊断→方案包)` → `G3(闸门→发布)` → `G4(T0/T1)` → `G5(AC-01)`。

### 3.2 可先行 vs 须等 A

分两档，避免误解「完全不能写代码」。

#### 3.2.1 硬阻塞：没有 A 就不能宣称该能力完成 / 不能过对应 GATE

| B 目标 | 等待 A | 缺了什么 | 影响 |
|--------|--------|----------|------|
| B0 官方交接 | **A-fixture** | `backend/tests/fixtures/handoff_a_to_b/` 四文件不存在 | 无标准交接包（可手写 mock，但非 A 交付） |
| B1 **真接**五区 | **A7 + A8**（另 A3/A0） | 真 `source_map`、确认版 keywords、`chat()`、channel_defaults | 无法过 **G2**；AC-06/07/08 真数据 |
| B3 真溯源生成 | **A2 + A3** | 稳定 `kb_facts.id` + 业务路径调 `chat()` | AC-02 端到端 |
| B4 合规禁词 | **A0** | `get_industry_pack(...).forbidden_words()` 等未接到机审 | AC-03；G3 一侧 |
| B5 托管页 AUTO | **A5** | 托管页 URL/Schema/写入约定 | AUTO 真发；SEMI **不**阻塞 |
| B6/B7 T0/Δ | **A7** | `baseline=true` 的 T0 与 T1 同构 | **G4**；AC-12 |
| B6 AC-13 | **A9**（+ B6 读 `target_engines`） | 设置页/PUT 改主攻 AI | 主攻 AI 联动验收 |
| 前端真鉴权 G1 | **A1**（后端多半已有）+ 登录页接真 JWT | Login stub | 下游页带真实 Bearer |

#### 3.2.2 可先行（MOCK_OK）：A 未完成时 B 仍应开发

| 任务 | 允许先做 | 代码备注要求 |
|------|----------|--------------|
| B0–B2 | UI + draft/confirm 契约形状 | `TODO(WAIT_FOR: A7+A8)` 在真接切换点 |
| B3 | 模板链、RAG 切片 JSON 结构、draft CRUD | `TODO(WAIT_FOR: A2+A3)` |
| B4 | 人闸门、approval_log、非禁词类机审 | `TODO(WAIT_FOR: A0)` 禁词接线 |
| B5 | SEMI 导出包、publish 状态机 | AUTO 处 `TODO(WAIT_FOR: A5)` |
| B6–B7 | 模拟监测、Dashboard 壳 | Δ/KPI 处 `TODO(WAIT_FOR: A7)` |
| B8 | 四页 API 封装接线 | 与后端 mock 联调 |

**接线原则：** A0 IndustryPack、A1 JWT、A2 KB、A3 Gateway 若仓库已有代码但未接到 B 业务路径——只读调用、不改 A 目录；缺接线时用 WAIT_FOR 提示 A；**不要**在 `content_service` 永久复制禁词表。

#### 3.2.3 依赖示意

```text
可 MOCK 先行链：
  B0 → B1(fixture) → B2 → B3(fixture KB) → B4(部分机审)
    → B5(SEMI) → B6(模拟监测) → B7(假 T0 KPI)

须等 A 才能真接/过线：
  A-fixture ──► B0 官方交接
  A7+A8(+A3/A0) ──► B1 真接 / G2
  A2+A3 ──► B3 真溯源
  A0 ──► B4 禁词 / AC-03
  A5 ──► B5 AUTO
  A7 ──► B6/B7 Δ · G4 · AC-12
  A9 ──► B6 AC-13
```

### 3.3 当前仓库快照（2026-07-16）

| 项 | 状态 |
|----|------|
| `handoff_a_to_b` fixture | **缺失**（可手写同结构 mock） |
| B 后端 CRUD + 模拟流水线骨架 | 多已有；非契约终态 |
| B1 真接 / G2 | **blocked** · WAIT_FOR A7+A8 |
| G4 T0/T1 Δ | **blocked** · WAIT_FOR A7 |
| B2 confirm / B5 SEMI | **可先做** |
| 进度表 A/B 行 | 初建多为 `todo`；以本手册契约 + 本快照为准，勿因半成品代码谎报 `done` |

**立即行动：**

1. 今天：B0 骨架 + 本地 mock；**NOTIFY A** 提交官方 fixture。  
2. 本周主线：B1（fixture）→ B2。  
3. 勿空等：SEMI、闸门 UI、Dashboard 壳可并行。  
4. 无 A7/A8 时 B1 只能标 `doing`/MOCK，**不得**标真接 `done` 或 G2 green。

---

## 4. 你从 A 拿到什么（交接包）

路径：`backend/tests/fixtures/handoff_a_to_b/`（**A 维护**；W1 可先手写同结构）。

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

| 字段 | 你用在 |
|------|--------|
| `diagnosis.source_map` | B1 渠道权重 `probe_weight` |
| `keywords` | B1 方案包 E 区 / scenario 候选 |
| `kb_facts[].id` | B3 `fact_refs` · B4 fact_verify |
| `enterprise.target_engines` | B6 EngineAdapter 范围 |
| T0（`baseline=true`） | B6/B7 算 Δ |

**GATE G2（约 W4）起**：B1 必须从 fixture 切到真实 `GET /diagnosis/{id}` + `GET /keywords`。

---

## 5. 阻塞时 · 提示开发者 A 的话术

### 缺 fixture

```text
【WAIT_FOR · 请通知开发者 A】
B0/B1 需要 handoff fixture：backend/tests/fixtures/handoff_a_to_b/
请按《开发者 B 手册》§4 结构提交 JSON（可先手写假数据）。
在就绪前：前端内联 mock，标注 TODO(WAIT_FOR: A-fixture)。
```

### B1 真接缺诊断/词库

```text
【WAIT_FOR · 请通知开发者 A】
我方正在实现：B1 方案包真接。
需要：A7 诊断（source_map）+ A8 确认版 keywords。
交付：GET /diagnosis/{id} · GET /keywords · 或更新 fixture。
验收：mixed_weight = 0.6*model + 0.4*probe。
此前继续 fixture（MOCK_OK），TODO(WAIT_FOR: A7+A8)。
```

### B1 缺 LLM Gateway

```text
【WAIT_FOR · 请通知开发者 A】
B1 需要 A3 gateway.chat()（至少 1 个 engine）。
禁止在 B 目录自建第二套 LLM 客户端；可用 JSON stub 顶五区。
```

### B3 缺 KB / chat

```text
【WAIT_FOR · 请通知开发者 A】
B3 内容工厂需要 A2 GET /kb/facts（供 fact_refs）+ A3 chat()。
此前可用 fixture kb_facts；TODO(WAIT_FOR: A2+A3)。
```

### B4 缺禁词

```text
【WAIT_FOR · 请通知开发者 A】
B4 需要 A0 IndustryPack.forbidden_words / banned_patterns / compliance_checklist。
禁止在 content_service 硬编码生美禁词副本。
```

### B5 真发托管页

```text
【WAIT_FOR · 请通知开发者 A】
B5 AUTO 需要 A5 托管页 URL 规则 + 写入点说明。
SEMI 导出包可先做；AUTO 暂停至约定清晰。
```

### B6/B7 缺 T0

```text
【WAIT_FOR · 请通知开发者 A】
B6/B7 需要 A7 写入 T0（monitor_results.baseline=true）。
缺则 GATE G4 不得标绿；UI 可用假 T0。
```

### 验 AC-13 缺设置页

```text
【WAIT_FOR · 请通知开发者 A】
AC-13 需要 A9（或 PUT /enterprise）能改 target_engines。
请提供入口后我方复测 monitor 引擎列表。
```

### B4/B5 完成后通知 A

```text
【NOTIFY · 请通知开发者 A】
B4 人闸门 + B5 发布已达联调标准。
可进入 GATE G3；请抽检托管页；准备 G4 的 T0 对齐。
```

---

## 6. 各任务输入 / 输出

### B1 · `GET /api/v1/user/strategy-pack/draft`

**依赖：** §4 交接包（真接时 WAIT_FOR A7+A8+A2）。

**权重公式：** `mixed_weight = model_weight × 0.6 + probe_weight × 0.4`

**输出五区（节选结构）：**

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

### B2 · `POST /api/v1/user/strategy-pack/confirm`

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

### B3–B4 · 草稿 · `GET /api/v1/user/content/drafts`

**约定：** `content_unit = 1 scenario × 1 channel × 1 skill`  
**fact_refs：** 必须是 `kb_facts.id[]`（来自 A）

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

| API | 输入 | 输出 |
|-----|------|------|
| `POST .../bulk-approve` | `{ "ids": [1,2,3] }` | `{ "approved": 3, "failed": [], "next_route": "/publish/tasks" }` + `approval_logs` |
| `POST .../{id}/reject` | `{ "reason": "..." }` | `{ "id": 1, "status": "draft" }` |

`approval_logs.target_type` = `strategy_pack+content`

**5 项机审：** fact_verify · 禁词 · 交叉验证 · 实体一致性 · RAG 可检索性

### B5 · 发布任务

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

SEMI 必填 `export_package`：

```json
{
  "title": "...",
  "body": "...",
  "tags": ["皮肤管理", "敏感肌"],
  "cover_hint": "使用 VISIA 检测过程图",
  "steps": ["打开小红书APP", "粘贴文案", "上传图片", "发布"]
}
```

`POST /publish/run` 输入：`{ "task_ids": [1, 2] }` → `{ "started": 2 }`

### B6 · 监测（T0/T1 同构）

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

- `baseline: true` → T0（**A 写**，你 WAIT_FOR A7）  
- `baseline: false` → T1（**你写**，发布 24h 后）

Core ~20 / Probe ≤10；引擎列表跟随 `enterprise.target_engines`。

### B7 · `GET /api/v1/user/outcomes/dashboard`

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

### B8 · 前端路由

| 路由 | 页面 | 调 API |
|------|------|--------|
| `/strategy-pack` | 方案包五区 + 词库折叠 | draft · confirm · keywords |
| `/content/drafts` | 草稿 + 人闸门 | drafts · bulk-approve / reject |
| `/publish/tasks` | 发布任务 | tasks · run |
| `/monitor` | T0/T1 · Core/Probe | profiles · results |
| `/outcomes` | 效果舱 | dashboard |

---

## 7. 枚举速查

| 项 | 取值 |
|----|------|
| 引擎 | `doubao` \| `deepseek` \| `kimi` \| `wenxin` |
| 渠道 | `hosted` \| `xiaohongshu` \| `zhihu` \| `dianping` \| `sohu` \| `toutiao` \| `wechat` |
| 发布模式 | `AUTO` \| `SEMI` \| `GUIDED` |
| 草稿状态 | `draft` \| `ready` \| `published` \| `rejected` |

**红线：** 禁止 Agent `write_fact` / `auto_confirm` / 直接 `publish`；正文不用 ReAct；跨租户 `403`；禁止为绕过 WAIT_FOR 改 A 目录。

---

## 8. 你参与的联调 GATE

| GATE | 你要交付 | 缺谁提示谁 |
|------|----------|------------|
| G1 | 任一受保护下游 API 鉴权正常 | 缺 JWT → 提示 A（A1） |
| G2 | B1 读真 diagnosis/keywords 五区正确 | 缺 A7/A8 → 提示 A；缺 B1 → 自己补 |
| G3 | B4+B5 | 缺 A0/A5 → 提示 A |
| G4 | B5+B6 写出 T1，能算 Δ | 缺 T0 → 提示 A |
| G5 | B 过线（§9） | 任一侧未过 → 提示该侧 |

---

## 9. 过线标准（个人）

勾选 ≤5 个 scenario → 草稿过 5 项机审 → 策略+草稿一次人闸门 → 托管页 AUTO + 小红书 SEMI → 效果舱可见 T0/T1 Δ。

**你侧重的 AC：** AC-01（后半）· AC-02 · AC-03 · AC-06～AC-13  

状态勾选写在 [G-L3-开发进度.md](G-L3-开发进度.md)。

---

## 10. Agent 开工检查清单（开发者 B）

```text
[ ] 已确认任务号 B0–B8 之一
[ ] 已读 G-L3-开发进度.md 本行状态与 A 前置是否 done
[ ] 已查本文 §3 依赖；有 WAIT_FOR 则展示 §5 话术，未改 A 目录
[ ] MOCK_OK 时只用 fixture/stub，并写 TODO(WAIT_FOR: …)
[ ] 完成且需 NOTIFY 时已提示 A，并更新开发进度表
[ ] 宣称 GATE/AC 前已核对 §8
[ ] 准备 git：progress: B<n> <todo|doing|blocked|done>
```

---

*开发者 B 手册 v1.1 · 强制顺序与 A 阻塞专章 · 进度以 G-L3-开发进度.md 为准*
