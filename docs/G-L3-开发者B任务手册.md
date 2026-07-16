# GEO 开发者 B · 下游任务手册

> **版本**：v1.2 | **日期**：2026-07-16  
> **你是谁**：开发者 B（下游）— 让方案能确认、写出稿、发出去、看出效果  
> **完整双人约定**：[G-L3-双人任务拆分.md](G-L3-双人任务拆分.md)  
> **进度同步（git）**：[G-L3-开发进度.md](G-L3-开发进度.md) — 只改其中「开发者 B」相关行  
> **API 契约**：[G-L3-API契约.md](G-L3-API契约.md) · **实施清单**：[G-L3-实施清单.md](G-L3-实施清单.md)  
> **v1.1**：§3.1–§3.3 强制顺序 · 可先行/须等 A · 仓库快照  
> **v1.2**：§11 逐步测试；**测试全部通过才允许验收 / 标 `done`**

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
| `验收` | **§11 测试全 PASS** 后才可标进度 `done`；失败则修或 `blocked` |
| 进度 | 改状态后更新 [G-L3-开发进度.md](G-L3-开发进度.md) 并 `git commit -m "progress: B…"` + `push` |

统一信封：`{ "code": 0, "data": {}, "msg": "ok" }` · Header：`Authorization: Bearer <JWT>`。

---

## 3. 任务总表（B0–B8）

| # | 任务 | 己方前置 | 跨人依赖 | 实施清单 | 验收（须 §11 测试 PASS） |
|---|------|----------|----------|:--------:|--------------------------|
| **B0** | 方案包/草稿页骨架（fixture mock） | — | **WAIT_FOR A-fixture** · `MOCK_OK` | — | T-B0-01～04 + 五区 UI |
| **B1** | persona + scenario + 权重 0.6/0.4 | B0 | **WAIT_FOR A7+A8**（真接）· **A3/A0** · `MOCK_OK` | 2.1–2.3 | T-B1-01～06（真接加 R01/R02） |
| **B2** | `POST /strategy-pack/confirm` | B1 | 无 | 2.4–2.5 | T-B2-01～05 |
| **B3** | 内容工厂：固定链 + 7 段式 + RAG 切片 | B2 | **WAIT_FOR A2+A3** · `MOCK_OK` | 2.6–2.8 | §11.4 B3 |
| **B4** | 5 项机审 + 人闸门 + `approval_log` | B3 | **WAIT_FOR A0**（禁词/合规） | 2.9–2.14 | §11.4 B4 · **NOTIFY A** |
| **B5** | 托管页 AUTO + 小红书 SEMI | B4 | **WAIT_FOR A5**（真发托管页时） | 3.1/3.3/3.5 | §11.4 B5 · **NOTIFY A** |
| **B6** | Core/Probe + T1 + T0/T1 Δ + Engine 联动 | B5 | **WAIT_FOR A7**（T0）· 验 AC-13 时 **WAIT_FOR A9** | 3.6–3.9/3.12 | §11.4 B6 |
| **B7** | 效果舱 Dashboard | B6 | **WAIT_FOR A7**（T0 KPI） | 3.14 | §11.4 B7 |
| **B8** | 前端：方案包/草稿/发布/监测/效果舱 | 随 B1–B7 | 真接继承上表 · `MOCK_OK` | — | §11.2 B8 |

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
5. **每步必须按 §11 跑测试；测试未通过一律不得验收、不得在进度表标 `done`。**

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

**验收前提（强制）：** 对应任务在 §11 的测试项全部勾选通过；MOCK 阶段只验收「MOCK 档」用例，真接档须等 A 交付后再测。

状态勾选写在 [G-L3-开发进度.md](G-L3-开发进度.md)；备注须写 `tests: B<n> pass` 或失败项 ID。

---

## 10. Agent 开工检查清单（开发者 B）

```text
[ ] 已确认任务号 B0–B8 之一
[ ] 已读 G-L3-开发进度.md 本行状态与 A 前置是否 done
[ ] 已查本文 §3 依赖；有 WAIT_FOR 则展示 §5 话术，未改 A 目录
[ ] MOCK_OK 时只用 fixture/stub，并写 TODO(WAIT_FOR: …)
[ ] 已按 §11 为该任务编写/更新测试并本地跑通
[ ] 完成且需 NOTIFY 时已提示 A，并更新开发进度表
[ ] 宣称 GATE/AC / 标 done 前：§11 该任务全部测试 PASS，已核对 §8
[ ] 准备 git：progress: B<n> done tests pass（失败则不得 done）
```

---

## 11. 逐步测试与验收门槛（强制）

### 11.0 铁律

| 规则 | 说明 |
|------|------|
| **先测后验** | 每个 Bx 开发完成后必须执行本节对应用例；**全部 PASS 才可验收** |
| **未测 = 未完成** | 进度表禁止将未测或有失败项的任务标为 `done` |
| **MOCK / 真接分档** | 先行期只要求「MOCK 档」PASS；标「真接 done」或 GATE 绿必须再跑「真接档」 |
| **失败即 blocked** | 测试失败：修代码或标 `blocked`（写清失败用例 ID），不得跳过 |
| **提交附带** | `progress: Bx done` 的 commit 备注或进度表「备注」列须含测试结果摘要 |

### 11.1 测试落盘约定

| 类型 | 建议路径 | 工具 |
|------|----------|------|
| 后端 API / service | `backend/tests/b_track/test_b0_….py` … `test_b8_….py` | pytest |
| 权重/机审纯函数 | 同目录 `test_b1_weights.py` `test_b4_review.py` | pytest |
| 前端页面烟雾 | 手工清单勾选（MVP）；有框架后再补 vitest/playwright | 手册勾选即可 |
| 已有冒烟参考 | `backend/scripts/smoke/smoke_test.py` | 可作联调辅助，**不替代** Bx 专项用例 |

命令（后端）：

```bash
cd backend
pytest tests/b_track/test_b0_skeleton.py tests/b_track/test_b1_strategy_pack.py tests/b_track/test_b2_confirm.py -q
```

（文件按任务逐步创建；无文件则该任务**不得**标 done。）

### 11.2 B0–B8 测试总表

| 任务 | 用例 ID 前缀 | MOCK 档（先行可验收） | 真接档（过 GATE / 真 done） | 建议命令 |
|------|--------------|----------------------|---------------------------|----------|
| B0 | T-B0-* | 五区+草稿页可渲染；mock JSON 符合 §4 形状 | 官方 `handoff_a_to_b` 可读 | 前端手测 + 可选 schema 校验脚本 |
| B1 | T-B1-* | `GET draft` 五区字段齐全；`mixed=0.6*m+0.4*p` | 读真 diagnosis/keywords；persona/scenario 非纯静态模板 | `pytest …/test_b1_*.py` |
| B2 | T-B2-* | confirm 落 `scenarios`+`strategy_packs`；返回 `next_route`；触发内容 Job/队列标记 | （无额外 A 依赖） | `pytest …/test_b2_*.py` |
| B3 | T-B3-* | drafts 含 `fact_refs`（fixture id）+ `rag_slices` 结构；7 段式骨架 | fact_refs 指向真实 KB；生成经 `chat()` | `pytest …/test_b3_*.py` |
| B4 | T-B4-* | bulk-approve/reject；`approval_log`；至少 fact_verify+实体类机审 | 禁词来自 IndustryPack；5 项全绿 | `pytest …/test_b4_*.py` |
| B5 | T-B5-* | SEMI `export_package` 五字段齐全；publish 状态机 | AUTO 托管页 URL 可访问+Schema | `pytest …/test_b5_*.py` |
| B6 | T-B6-* | Core/Probe 配置；可写 T1（`baseline=false`） | 与 T0 对齐算 Δ；跟随 `target_engines` | `pytest …/test_b6_*.py` |
| B7 | T-B7-* | dashboard 返回 kpi/funnel 壳 | `delta_mention` 来自真 T0/T1 | `pytest …/test_b7_*.py` |
| B8 | T-B8-* | 五页路由可开；API 封装非硬编码假数据（可 mock 层） | 带真 JWT 调下游 API | 手测清单 + 后续 E2E |

### 11.3 先行任务详细用例（B0 → B1 → B2）

> 本周主线。以下每条必须有「操作 → 期望」；全部 PASS 才允许该任务 MOCK 验收。

#### B0 · UI 骨架（MOCK）

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-B0-01 | 手测 | 登录后打开 `/strategy-pack` | 页面不白屏；可见五区占位（A–E） | ☐ |
| T-B0-02 | 手测 | 打开 `/content/drafts` | 可见草稿列表区（可为空或 mock 行） | ☐ |
| T-B0-03 | 校验 | mock/fixture JSON 对照 §4 | 含 `enterprise` / `diagnosis.source_map` / `keywords` / `kb_facts` 键 | ☐ |
| T-B0-04 | 代码 | 真接切换点 | 存在 `TODO(WAIT_FOR: A-fixture)` 或等价注释 | ☐ |

**B0 MOCK 验收：** T-B0-01～04 全 PASS。官方 fixture 未交付不算「交接完成」，但 MOCK 可 done。

#### B1 · 方案包 draft（MOCK 先行）

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-B1-01 | API | `GET /api/v1/user/strategy-pack/draft`（带 JWT） | `code=0`；`data` 含 persona / competitors / scenarios / channels / keywords | ☐ |
| T-B1-02 | 单测 | 给定 model_weight=0.4, probe_weight=0.1 | `mixed_weight == 0.28`（允许浮点误差 1e-6） | ☐ |
| T-B1-03 | API | 检查 `scenarios.candidates` | 为数组；`max<=5`；元素含 `id,user_query,channel,skill` | ☐ |
| T-B1-04 | API | 检查 `channels[]` | 每项含 `model_weight,probe_weight,mixed_weight` | ☐ |
| T-B1-05 | 手测 | 方案包页渲染 draft | 五区有数据（可来自 fixture）；无控制台致命错误 | ☐ |
| T-B1-06 | 代码 | 真接切换点 | `TODO(WAIT_FOR: A7+A8)` | ☐ |

**B1 真接档（A7+A8 后加测，不过 G2 可不跑）：**

| ID | 操作 | 期望 |
|----|------|------|
| T-B1-R01 | draft 的渠道权重 | `probe_weight` 来自真实 `source_map`（非写死） |
| T-B1-R02 | keywords E 区 | 与 `GET /keywords` 一致（租户内） |

**B1 MOCK 验收：** T-B1-01～06 全 PASS。真接 done / G2：再加 T-B1-R01/R02。

#### B2 · confirm（无跨人硬依赖）

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-B2-01 | API | `POST …/strategy-pack/confirm` body 含 2 个 `selected_scenarios` | `code=0`；`strategy_pack_id` 有值；`next_route` 含 `/content/drafts` | ☐ |
| T-B2-02 | DB/API | confirm 后再查 scenarios | 已选场景已落库且 `enterprise_id` 正确 | ☐ |
| T-B2-03 | 行为 | confirm 后 | 内容生成 Job 被触发（task 状态 pending/running 或 drafts 开始出现） | ☐ |
| T-B2-04 | 负例 | 未选 scenario 或超过 max | 返回 4xx，不落 pack | ☐ |
| T-B2-05 | 租户 | 用另一租户 token 读该 pack | `403` 或空（不得串数据） | ☐ |

**B2 验收：** T-B2-01～05 全 PASS → 可标 `done`。

### 11.4 B3–B8 最低测试要求（摘要）

实现到该步时，必须把下表展开为与 B0–B2 同级的勾选表（可复制到 PR / 进度备注）。

| 任务 | 最低必测（MOCK） | 真接加测 |
|------|------------------|----------|
| B3 | 生成 drafts≥1；每条有 `rag_slices`（title/summary/body/chars）；`fact_refs` 非空数组 | refs∈真实 kb_facts；生成调用 gateway |
| B4 | reject 回 draft；bulk-approve 写 approval_log；`target_type=strategy_pack+content` | 禁词命中拒发；5 项 `machine_review` |
| B5 | SEMI 包含 title/body/tags/cover_hint/steps；`content_asset_id` 可追溯 | AUTO URL 200 + Schema 片段 |
| B6 | 可创建 Core/Probe profile；写入 T1 结果 | 与 T0 同 prompt 算 Δ；改 engines 后监测范围变 |
| B7 | dashboard JSON 含 kpi + funnel 四层键 | delta 与 monitor 汇总一致 |
| B8 | 五路由可进；关键按钮触发真实 API（或统一 mock 层） | Bearer 有效；401 未登录 |

### 11.5 GATE 测试（联调日）

| GATE | 测试要点 | 未通过时 |
|------|----------|----------|
| G1 | 无 JWT → 401；有 JWT → 下游 API 200 | 提示 A1 / 修 Login |
| G2 | B1 真接档 PASS | 提示 A7/A8 或修 B1 |
| G3 | B4+B5 对应用例 PASS | 提示 A0/A5 |
| G4 | T0+T1 可算 `delta_mention` | 提示 A7 |
| G5 | §9 路径手工走通 + 相关 Bx 测试绿 | 两侧分别修 |

### 11.6 验收记录模板（贴进度表备注）

```text
任务: B2
档: MOCK|真接
命令: pytest tests/b_track/test_b2_confirm.py -q
结果: PASS (T-B2-01..05)
日期: YYYY-MM-DD
```

失败示例：

```text
任务: B1
结果: FAIL T-B1-02 mixed_weight 期望 0.28 实际 0.25
处置: blocked / 修复中，不得 done
```

---

## 12. 推荐先行执行清单（本周）

按顺序做；**每步结束跑 §11.3，PASS 再进下一步。**

| 步 | 任务 | 开发要点 | 测试 | 验收条件 | 前端可看？ |
|:--:|------|----------|------|----------|------------|
| 1 | B0 | 五区+草稿骨架；手写 §4 同构 mock | T-B0-01～04 | MOCK PASS | **可以** — `/strategy-pack` 看 A–E 区；`/content/drafts` 看列表 |
| 2 | B1 | draft API + 权重公式 + 页渲染 | T-B1-01～06 | MOCK PASS | **可以** — 同页刷新草案；黄条表示 MOCK |
| 3 | B2 | confirm + 落库 + 触发生成 | T-B2-01～05 | 全 PASS | **部分可以** — 勾选 scenario 点确认；无真 JWT/后端时会 MOCK 跳转草稿页 |
| 并行 | B8 局部 | 先接 strategy/content API | 手测路由 | 不单独阻塞 B2 | 同上 |
| 勿做 | B1 真接 / G2 | — | — | WAIT_FOR A7+A8 | — |

### 12.1 前端查看步骤（B0–B2）

1. 启动前端：`cd frontend && npm run dev`（默认 http://localhost:5173）
2. 打开登录页，用占位账号进入（当前 Login 仍为 demo-token stub，**属 A1 范围**；有 token 即可进后台）
3. 侧栏进入 **方案包** `/strategy-pack` → 应看到 **A–E 五区**；顶部可能有 MOCK 黄条
4. 勾选 1–2 个 scenario → **确认方案包** → 跳转 **内容草稿** `/content/drafts`
5. 草稿页应有列表区（MOCK 两行或空列表提示）

**不能当真接验收的：** 无 A7/A8 时五区数据非探针实测；无后端 JWT 时 confirm 不落库。

```text
【NOTIFY · 请通知开发者 A】（B0 开工时发送）
请提交 backend/tests/fixtures/handoff_a_to_b/ 官方四文件（enterprise/diagnosis/keywords/kb_facts）。
B 侧暂用 enterprise_bundle.json MOCK；G2 前需你方 A7+A8 真接。
```

---

*开发者 B 手册 v1.2 · 逐步测试强制验收 · 进度以 G-L3-开发进度.md 为准*
