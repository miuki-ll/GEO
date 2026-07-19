# GEO 开发者 A · 上游任务手册

> **版本**：v1.0 | **日期**：2026-07-16  
> **你是谁**：开发者 A（上游）— 让店能登录、建库、跑出诊断和词库  
> **完整双人约定**：[G-L3-双人任务拆分.md](G-L3-双人任务拆分.md)  
> **进度同步（git）**：[G-L3-开发进度.md](G-L3-开发进度.md) — 只改其中「开发者 A」相关行  
> **API 契约**：[G-L3-API契约.md](G-L3-API契约.md) · **实施清单**：[G-L3-实施清单.md](G-L3-实施清单.md)

---

## 0. 一句话范围

| 你负责 | 你不负责（开发者 B） |
|--------|----------------------|
| 舱1 懂我 + 平台底座 | 舱2 定方案 + 舱3 出结果 |
| 管道步骤 1→3：入驻 · 诊断 · 词库 | 策略 · 内容 · 检测 · 人闸门 · 发布 · 监控 · 效果舱 |
| FR-ON / FR-DG / FR-KW | FR-SP / FR-CF / FR-CK / FR-GT / FR-PB / FR-MN / FR-CV |

**对外用户路径（你交付的前半段）：**

```
注册/登录 → 入驻(选主攻AI) → 诊断(探针LLM·5项) → 四层词库 → T0基线
                                                                      │
                                                          B 从这开始 ──┘
```

---

## 1. 代码目录（只改这些）

| 层 | 路径 |
|----|------|
| API | `backend/app/api/v1/auth.py` · `backend/app/api/v1/user/enterprise.py` · `backend/app/api/v1/user/kb.py` · `backend/app/api/v1/user/onboarding.py` · `backend/app/api/v1/user/diagnosis.py` |
| 鉴权 | `backend/app/core/security.py` · `backend/app/api/deps/auth.py` · `backend/app/api/common.py` |
| Service | `backend/app/service/auth_service.py` · `backend/app/service/kb_service.py` · `backend/app/service/diagnosis_service.py` · `backend/app/service/kb_freshness_service.py` |
| LLM | `backend/app/core/llm/gateway.py` · `backend/app/core/llm/adapters.py` · `backend/app/core/llm/base.py` · `backend/app/core/llm/schemas.py` |
| Embedding | `backend/app/core/embedding.py`（或 `backend/app/rag/`） |
| Agent | `backend/app/agents/graphs/onboarding/` · `backend/app/agents/industry/` · `backend/app/agents/registry.py` · `backend/app/agents/runner.py` |
| 前端 | `frontend/src/views/Login.vue` · `Register.vue` · `frontend/src/views/onboarding/` · `frontend/src/views/knowledge-base/` · `frontend/src/views/settings/` · `frontend/src/api/auth.ts` · `enterprise.ts` · `kb.ts` · `onboarding.ts` |
| 表 | `enterprises` · `users` · `brands` · `stores` · `services` · `kb_facts` · `kb_faqs` · `kb_signals` · `kb_externals` · `source_diagnoses` · `keywords` · `target_engines` · `agent_tasks` · `faiss_indexes` |
| Fixture | `backend/tests/fixtures/handoff_a_to_b/`（**你维护**，四文件） |

**禁止改：** `strategy_pack.py` · `content.py` · `publish.py` · `monitoring.py` · `outcomes.py` · `strategy_service.py` · `scenario_service.py` · `content_service.py` · `publish_service.py` · `monitor_service.py` · `dashboard_service.py` · 前端 `strategy/` · `content/` · `publish/` · `monitor/` · `outcomes/`（属 B）。

**B 只读调用你维护的：** `gateway.chat()` · `IndustryPack.forbidden_words()` 等 · `kb_facts.id` · `GET /diagnosis/{id}` · `GET /keywords`

**共建（PR 双方 review）：** `G-L3-API契约.md` · 跨域 `models/` / `schemas/` · Alembic。

---

## 2. 依赖协议（Agent 必读）

| 标记 | 你怎么做 |
|------|----------|
| `依赖: 无` | 可直接实现，不依赖任何人 |
| `依赖: 己方 Ax` | 先完成前置己方任务，再开始本任务 |
| `WAIT_FOR: Bx` | **唯一跨人阻塞点**（仅 A9 验收 AC-13 时）；不要改 B 的目录；向用户展示 §5 话术通知 B |
| `NOTIFY: B` | 完成后提示 B 可开始/继续对应任务 |
| `GATE` | 联调闸门；双方都完成后才算过线 |
| 进度 | 改状态后更新 [G-L3-开发进度.md](G-L3-开发进度.md) 并 `git commit -m "progress: A…"` + `push` |

统一信封：`{ "code": 0, "data": {}, "msg": "ok" }` · Header：`Authorization: Bearer <JWT>`。

---

## 3. 任务总表（A0–A9）

| # | 任务 | 己方前置 | 跨人依赖 | 实施清单 | 验收（须测试 PASS） |
|---|------|----------|----------|:--------:|---------------------|
| **A0** | IndustryPack 基类 + `beauty_local` 规则簿 | — | 无 · **NOTIFY B** | 0.1 · 0.2 | `get_industry_pack("beauty_local")` 可取禁词/合规/渠道/few-shot |
| **A1** | 注册/登录/JWT/RBAC/租户隔离 | — | 无 · **NOTIFY B** | — | 跨 enterprise API → `403` |
| **A2** | KB CRUD（Fact/FAQ/Signal/External） | A1 | 无 · **NOTIFY B** | — | `kb_facts.id` 可被 B 的 `fact_refs` 引用 |
| **A3** | LLM Gateway × 4 EngineAdapter | — | 无 · **NOTIFY B** | 0.4 | 统一 `chat()`；豆包/DeepSeek/Kimi/文心通 |
| **A4** | Faiss per-tenant 向量库 | A1 | 无 · **NOTIFY B** | 0.3 | 按 `enterprise_id` 隔离 add/search |
| **A5** | 开店向导 API：建库 + Schema + llms.txt + 激活行业包 | A0 A1 A2 | 无 | 1.1 · 1.2 | `POST /onboarding/run` → `{ task_id }` |
| **A6** | onboarding SSE 进度 | A5 | 无 | 0.5 · 1.3 | `progress_pct` 到 100 + `next_route` |
| **A7** | 诊断 5 项 + 写 T0 | A3 A5 A6 | 无 · **NOTIFY B**（解锁 B1/B6） | 1.4–1.8 | `GET /diagnosis/{id}` 字段齐全；T0 入库 |
| **A8** | 四源汇聚词库 + CRUD + generate | A4 A7 | 无 · **NOTIFY B**（解锁 B1 真接） | 1.9 · 1.10 | 四层 + 来源标注 + 租户隔离 |
| **A9** | 前端：登录/入驻/KB/设置（含改 `target_engines`） | A1 A5 | 验 AC-13 时 **WAIT_FOR B6** | 1.1 · 4.1 | 入驻完成可跳转 `/strategy-pack`；改引擎后监测跟随 |

### 3.1 开发顺序（强制依赖）

**己方严格串行：** `A0 → A3 → A4`（可并行）→ `A1 → A2 → A5 → A6 → A7 → A8 → A9`

```
W1: A0 + A1 + A2 + A3 + A4（底座平铺，互不依赖的可并行）
W2: A5 + A6（入驻+SSE）
W3: A7（诊断+T0）
W4: A8（词库）
W5–W8: A9（前端）+ 联调修补
```

### 3.2 可先行 vs 须等 B

A 轨大部分任务**不依赖 B**，只有一处跨人阻塞：

| A 目标 | 等待 B | 缺了什么 | 影响 |
|--------|--------|----------|------|
| A9 验收 AC-13 端到端 | **B6** | 监测跟随 `target_engines` 切换未实现 | 只能先做设置页 UI，联动验收暂停 |

其他 9 个任务（A0–A8）全部无跨人依赖，可独立完成。

### 3.3 当前仓库快照（2026-07-16）

| 模块 | 状态 | 说明 |
|------|------|------|
| Auth（A1） | 🟡 已有 | `auth.py` register/login 就绪；JWT 在 `core/security.py`；需确认租户隔离完备 |
| Enterprise（A1） | 🟡 已有 | profile/members CRUD 就绪；`target_engines` 更新待确认 |
| KB CRUD（A2） | 🟢 已有 | Fact/FAQ/Signal/External 四表 CRUD 路由+服务就绪 |
| LLM Gateway（A3） | 🟢 已有 | 4 Adapter（doubao/deepseek/kimi/wenxin）+ `chat()` 统一入口就绪 |
| IndustryPack（A0） | 🟢 已有 | 基类 ABC + `beauty_local` 规则簿（禁词/渠道/人设/合规）就绪 |
| Faiss（A4） | 🔴 空壳 | `FaissIndex` model 存在，`rag/__init__.py` 只有注释，无实际实现 |
| Onboarding（A5/A6） | 🟡 骨架 | `/onboarding/run` 路由存在，Agent graph 仅注册未实现节点 |
| Diagnosis（A7） | 🟡 部分 | pain/persona/competitor 三个 GET + `/all` POST 存在；缺完整 5 项诊断 + T0 写入 |
| Keywords（A8） | 🔴 缺失 | 词库模块未见独立路由/服务；需新建 |
| Fixture（handoff） | 🟢 已交付 | `enterprise.json` · `diagnosis.json` · `keywords.json` · `kb_facts.json` 四文件就绪 |
| 前端（A9） | 🟡 骨架 | Login/Register/onboarding/knowledge-base/settings 目录存在，待完善接线 |

**立即行动：**

1. 今天：A4 Faiss 实现；确认 A1 租户隔离覆盖所有 A 路由。
2. 本周主线：A5 入驻 graph 节点实现 → A6 SSE。
3. 勿空等：A 轨无 B 阻塞，A0–A8 可全速推进。
4. 每步必须按 §11 跑测试。

---

## 4. 关键输入 / 输出

### A0 · IndustryPack 产出

**B 消费方式（只读调用）：**

```python
from app.agents.industry.registry import get_industry_pack

pack = get_industry_pack("beauty_local")
pack.forbidden_words()      # → List[str]   B4 禁词机审用
pack.channel_weights()      # → List[dict]  B1 渠道权重参考
pack.default_persona()      # → dict        B1 persona 提示词
pack.compliance_checklist() # → List[str]   B4 合规检查用
```

### A1 · 鉴权产出

- JWT 签发：`POST /api/v1/auth/login` → `{ access_token, token_type: "bearer" }`
- 租户隔离：所有 A/B 路由通过 `get_current_user` 注入 `user.enterprise_id`，跨租户访问返回 `403`

### A5 · 入驻 `POST /api/v1/user/onboarding/run`

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

**副作用：** 写 Brand / Store / Service / KBFact / KBSignal；激活 IndustryPack；生成托管页骨架 + Schema + llms.txt。

### A6 · 进度 SSE `GET /api/v1/user/onboarding/status/{task_id}`

**流式输出：**

```json
{ "step": "DIAGNOSE", "progress_pct": 25, "progress_message": "DIAGNOSE done" }
```

**完成时：**

```json
{ "progress_pct": 100, "next_route": "/strategy-pack?draft=1" }
```

> **跨人提示：** SSE 完成后前端会跳转 B 的 `/strategy-pack`。若 B0/B1 页面未就绪，提示 B 优先保证路由可打开。

### A7 · 诊断 `GET /api/v1/user/diagnosis/{id}`

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

### A8 · 词库标准形状

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

---

## 5. 通知开发者 B 的话术

### A0 完成后

```text
【NOTIFY · 请通知开发者 B】
A0 IndustryPack 已完成。
你可在 B4 检测中调用：forbidden_words / banned_patterns / compliance_checklist。
你可在 B1 使用：channel_defaults / persona_hint / scenario_few_shot。
路径：agents/industry/packs/beauty_local/
```

### A1 / A2 / A3 完成后（合并可发）

```text
【NOTIFY · 请通知开发者 B】
底座已就绪：JWT(A1) · KB CRUD(A2) · LLM Gateway chat()(A3)。
你可开始/继续：B1（调 chat）· B3（kb_fetch + fact_refs 指向真实 kb_facts.id）。
请确认请求头带 Authorization: Bearer <JWT>。
```

### A4 完成后

```text
【NOTIFY · 请通知开发者 B】
A4 Faiss per-tenant 向量库已就绪。
你可复用向量检索做 scenario/词库去重（B1）。
```

### A7 完成后（关键）

```text
【NOTIFY · 请通知开发者 B · 解锁 B1 真接 / B6 Δ】
A7 诊断已完成。
请消费：
  - GET /api/v1/user/diagnosis/{id}（含 source_map.rankings / gaps）
  - T0：monitor_results 或等价基线，baseline=true
请将 B1 从 fixture 切换为真实 diagnosis；B6 可用 T0 算 Δ。
契约：G-L3-API契约.md §4 · §9
```

### A8 完成后（关键）

```text
【NOTIFY · 请通知开发者 B · 解锁 B1 词库区真接】
A8 词库已完成。
请消费：GET /api/v1/user/keywords（四层 + source + lbs_tags）。
B1 方案包 E 区与 scenario 候选请改读真实 keywords，停用 mock。
```

### A9 做到「验收主攻 AI 联动」时（唯一需要等 B 的地方）

```text
【WAIT_FOR · 请通知开发者 B】
我方正在验收 A9 / AC-13：修改 target_engines 后监测应切换。
需要对方先完成：B6（Core/Probe 监测已按 enterprise.target_engines 选 EngineAdapter）。
请 B 确认：PUT /enterprise { target_engines } 之后，下次 monitor_run 引擎列表已变。
在 B6 完成前：A9 设置页 UI 可先做，端到端联动验收暂停。
```

---

## 6. 枚举速查

| 项 | 取值 |
|----|------|
| 引擎 | `doubao` \| `deepseek` \| `kimi` \| `wenxin` |
| 渠道 | `hosted` \| `xiaohongshu` \| `zhihu` \| `dianping` \| `sohu` \| `toutiao` \| `wechat` |
| 词库 layer | `认知层` \| `选型层` \| `痛点层` \| `场景层` |
| 词库 source | `RawInputs` \| `探针反推` \| `SEO API` \| `LLM生成` \| `手动` |
| 发布模式 | `AUTO` \| `SEMI` \| `GUIDED` |
| 分页 | `?page=1&page_size=20` → `{ items, total, page, page_size }` |
| 异步 | `202` + `{ task_id, status }`；进度用 SSE |

**红线：** 禁止 Agent `write_fact` / `auto_confirm` / 直接 `publish`；正文不用 ReAct；跨租户 `403`；禁止为绕过 WAIT_FOR 改 B 目录；**IndustryPack 规则簿由你维护，B 只读调用**。

---

## 7. 你参与的联调 GATE

| GATE | 你要交付 | 缺谁提示谁 |
|------|----------|------------|
| G1 | A1 JWT 签发 + 租户隔离 | 缺 → 自己补 A1 |
| G2 | A7 真 diagnosis + A8 真 keywords → B1 可读 | 缺 B1 → 提示 B |
| G3 | A0 禁词可用 + A5 托管页可挂 | 缺 B4/B5 → 提示 B |
| G4 | A7 T0（`baseline=true`）→ B 可算 Δ | 缺 T1 → 提示 B（B6） |
| G5 | A 过线（§9） | 任一侧未过 → 提示该侧 |

---

## 8. 过线标准（个人）

入驻选主攻 AI → SSE 跑完 → GEO 健康报告可读 → 四层词库可编辑 → T0 入库 → 设置页可改 `target_engines`。

**你侧重的 AC：** AC-01（前半）· AC-04 · AC-05 · AC-14 · AC-15

**验收前提（强制）：** 对应任务在 §11 的测试项全部勾选通过。

---

## 9. 交接 fixture（你维护）

路径：`backend/tests/fixtures/handoff_a_to_b/`

| 文件 | B 用在 | 更新时机 |
|------|--------|----------|
| `enterprise.json` | B1/B5/B6 | A5 完成后按真实 schema 刷新 |
| `diagnosis.json` | B1/B6/B7 | A7 完成后按真实输出形状刷新 |
| `keywords.json` | B1 | A8 完成后按真实四层结构刷新 |
| `kb_facts.json` | B3/B4 | A2 完成后按真实字段刷新 |

**B 在 GATE G2（约 W4）前可用 fixture mock；G2 起必须切真实 API。**

---

## 10. Agent 开工检查清单（开发者 A）

```text
[ ] 已确认任务号 A0–A9 之一
[ ] 已读 G-L3-开发进度.md 本行状态
[ ] 已查本文 §3 依赖；有 NOTIFY 则在完成后发话术；有 WAIT_FOR 则展示 §5 话术
[ ] 未改 B 目录代码（§1）
[ ] 已按 §11 为该任务编写/更新测试并本地跑通
[ ] 完成且需 NOTIFY 时已提示 B，并更新开发进度表
[ ] 若产出影响 fixture 形状，已同步更新 handoff_a_to_b/ 对应文件
[ ] 宣称 GATE/AC / 标 done 前：§11 该任务全部测试 PASS
[ ] 准备 git：progress: A<n> done tests pass
```

---

## 11. 逐步测试与验收门槛（强制）

### 11.0 铁律

| 规则 | 说明 |
|------|------|
| **先测后验** | 每个 Ax 开发完成后必须执行本节对应用例；**全部 PASS 才可验收** |
| **未测 = 未完成** | 进度表禁止将未测或有失败项的任务标为 `done` |
| **失败即 blocked** | 测试失败：修代码或标 `blocked`（写清失败用例 ID），不得跳过 |
| **提交附带** | `progress: Ax done` 的 commit 备注或进度表「备注」列须含测试结果摘要 |

### 11.1 测试落盘约定

| 类型 | 建议路径 | 工具 |
|------|----------|------|
| 后端 API / service | `backend/tests/a_track/test_a0_industry_pack.py` … `test_a8_keywords.py` | pytest |
| LLM Gateway / 适配器 | 同上，`test_a3_gateway.py` | pytest + mock |
| Faiss 向量库 | `backend/tests/a_track/test_a4_faiss.py` | pytest |
| 前端页面烟雾 | 手工清单勾选（MVP） | 手册勾选 |
| 已有冒烟参考 | `backend/scripts/smoke/smoke_test.py` | 联调辅助 |

命令（后端）：

```bash
cd backend
pytest tests/a_track/ -q
```

（文件按任务逐步创建；无文件则该任务**不得**标 done。）

### 11.2 A0–A9 测试总表

| 任务 | 用例 ID 前缀 | 最低必测 | 建议命令 |
|------|-------------|----------|----------|
| A0 | T-A0-* | `get_industry_pack("beauty_local")` 返回非空 forbidden_words / channel_weights / default_persona / compliance_checklist | `pytest tests/a_track/test_a0_*.py` |
| A1 | T-A1-* | register → 得 JWT；login → 得 JWT；跨租户访问 → 403；无 token → 401 | `pytest tests/a_track/test_a1_*.py` |
| A2 | T-A2-* | Fact CRUD；FAQ CRUD；Signal CRUD；External CRUD；租户隔离 | `pytest tests/a_track/test_a2_*.py` |
| A3 | T-A3-* | `gateway.chat()` 四个 engine 均可返回 content；异常 engine fallback | `pytest tests/a_track/test_a3_*.py` |
| A4 | T-A4-* | add + search 同租户可见；跨租户不可见；delete 生效 | `pytest tests/a_track/test_a4_*.py` |
| A5 | T-A5-* | `/onboarding/run` → task_id；写 Brand/Store/Service/KBFact/KBSignal | `pytest tests/a_track/test_a5_*.py` |
| A6 | T-A6-* | SSE 推送 progress_pct 递增到 100 + next_route | `pytest tests/a_track/test_a6_*.py` |
| A7 | T-A7-* | diagnosis 五区字段齐全；T0 写入 baseline=true | `pytest tests/a_track/test_a7_*.py` |
| A8 | T-A8-* | 四层词库 CRUD + generate；租户隔离；keyword.layer 枚举校验 | `pytest tests/a_track/test_a8_*.py` |
| A9 | T-A9-* | 登录页可注册/登录；入驻页可提交；KB 页可编辑；设置页可改 engines | 手测清单 |

### 11.3 先行任务详细用例（A0 → A1 → A2 → A3）

> 本周主线（W1 底座）。以下每条必须有「操作 → 期望」；全部 PASS 才允许该任务验收。

#### A0 · IndustryPack（已有代码，补测）

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-A0-01 | 单测 | `from app.agents.industry.registry import get_industry_pack; p = get_industry_pack("beauty_local")` | 不抛异常，`p.code == "beauty_local"` | ☐ |
| T-A0-02 | 单测 | `p.forbidden_words()` | 返回 `List[str]`，非空（含至少 5 个禁词） | ☐ |
| T-A0-03 | 单测 | `p.channel_weights()` | 返回 `List[dict]`，每项含 name/weight | ☐ |
| T-A0-04 | 单测 | `p.default_persona()` | 返回 dict，含 role/age_range/pain_tags 等字段 | ☐ |
| T-A0-05 | 单测 | `p.compliance_checklist()` | 返回 `List[str]`，非空 | ☐ |
| T-A0-06 | 单测 | `p.templates()` | 返回 dict，含上述五键 | ☐ |

**A0 验收：** T-A0-01～06 全 PASS → 可标 `done`，发 NOTIFY B。

#### A1 · 鉴权 + 租户隔离

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-A1-01 | API | `POST /api/v1/auth/register` 注册新企业 | `code=0`，返回 `access_token` | ☐ |
| T-A1-02 | API | `POST /api/v1/auth/login` 登录 | `code=0`，返回 `access_token` | ☐ |
| T-A1-03 | API | 无 token 访问 `/user/enterprise/profile` | `401` | ☐ |
| T-A1-04 | API | 用企业 A 的 token 访问企业 B 的 KB facts | `403` 或空结果（不得串数据） | ☐ |
| T-A1-05 | API | `PUT /user/enterprise/profile` 更新 `target_engines` | `code=0`，落库成功 | ☐ |

**A1 验收：** T-A1-01～05 全 PASS → 可标 `done`，发 NOTIFY B。

#### A2 · KB CRUD

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-A2-01 | API | `POST /user/kb/facts` 创建 fact | `code=0`，返回带 `id` 的 fact | ☐ |
| T-A2-02 | API | `GET /user/kb/facts?page=1&page_size=10` | 分页返回，items 含刚创建的 fact | ☐ |
| T-A2-03 | API | `PUT /user/kb/facts/{id}` 更新 | `code=0`，字段已更新 | ☐ |
| T-A2-04 | API | `DELETE /user/kb/facts/{id}` | `code=0`，再查 404 或不在列表 | ☐ |
| T-A2-05 | API | FAQ / Signal / External 同理 CRUD | 四表均可增删改查 | ☐ |
| T-A2-06 | 租户 | 企业 B token 读企业 A 的 fact | `403` 或空 | ☐ |

**A2 验收：** T-A2-01～06 全 PASS → 可标 `done`，发 NOTIFY B。

#### A3 · LLM Gateway

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-A3-01 | 单测 | `gateway.chat("你好", engine="doubao")` | 返回 `LLMResponse`，content 非空 | ☐ |
| T-A3-02 | 单测 | `gateway.chat("你好", engine="deepseek")` | 同上，不抛异常 | ☐ |
| T-A3-03 | 单测 | `gateway.chat("你好")` 不指定 engine | 按 `ENGINE_ORDER` fallback，最终有响应 | ☐ |
| T-A3-04 | 单测 | 模拟 engine 全部不可用 | 抛出明确异常，不静默返回空 | ☐ |
| T-A3-05 | 单测 | `gateway.embed("测试文本")` | 返回 `EmbeddingResponse`，vector 非空 | ☐ |

**A3 验收：** T-A3-01～05 全 PASS → 可标 `done`，发 NOTIFY B。

#### A4 · Faiss per-tenant

| ID | 类型 | 操作 | 期望 | PASS? |
|----|------|------|------|:-----:|
| T-A4-01 | 单测 | 向企业 1 的索引 add 向量，search 同 tenant | 返回结果，命中 | ☐ |
| T-A4-02 | 单测 | 企业 1 add 后，企业 2 search 同 query | 不返回企业 1 的数据 | ☐ |
| T-A4-03 | 单测 | delete 某向量后 search | 不再命中已删向量 | ☐ |

**A4 验收：** T-A4-01～03 全 PASS → 可标 `done`，发 NOTIFY B。

### 11.4 A5–A8 最低测试要求（摘要）

实现到该步时，必须把下表展开为与 A0–A4 同级的勾选表。

| 任务 | 最低必测 |
|------|----------|
| A5 | `/onboarding/run` → task_id；Brand/Store/Service/KBFact/KBSignal 落库；`target_engines` 写入 `enterprise`；IndustryPack 激活标记 |
| A6 | SSE `progress_pct` 递增到 100；`next_route` 含 `/strategy-pack`；中途断线重连可恢复 |
| A7 | diagnosis 五个维度（pain/persona/competitor/source_map/probe）字段齐全；T0 `baseline=true` 写入 `monitor_results`；不同 engine 诊断结果隔离 |
| A8 | keyword CRUD；四层分类 + 来源标注 + LBS；generate 调 LLM 产出候选词；租户隔离 |

### 11.5 GATE 测试（联调日）

| GATE | 测试要点 | 未通过时 |
|------|----------|----------|
| G1 | B 带 JWT 调下游 API 正常；无 JWT → 401 | 检查 A1 租户隔离 |
| G2 | B1 读真 diagnosis + keywords 五区正确 | 检查 A7/A8 输出形状 |
| G3 | B4 禁词来自 IndustryPack；B5 AUTO 托管页可访问 | 检查 A0/A5 |
| G4 | T0+T1 可算 `delta_mention` | 检查 A7 T0 写入 |
| G5 | 全链路 8 步 + A 侧测试绿 | A 侧自修 |

### 11.6 验收记录模板（贴进度表备注）

```text
任务: A3
命令: pytest tests/a_track/test_a3_gateway.py -q
结果: PASS (T-A3-01..05)
日期: 2026-07-16
```

失败示例：

```text
任务: A4
结果: FAIL T-A4-02 跨租户隔离未生效
处置: blocked / 修复中，不得 done
```

---

## 12. 推荐先行执行清单（本周 W1）

按顺序做；**每步结束跑 §11，PASS 再进下一步。**

| 步 | 任务 | 开发要点 | 测试 | 验收条件 |
|:--:|------|----------|------|----------|
| 1 | A0 | 已有代码；确认 registry 可加载 beauty_local | T-A0-01～06 | 全 PASS → `A0 done`，NOTIFY B |
| 2 | A3 | 已有代码；确认 4 engine 均可 chat | T-A3-01～05 | 全 PASS → `A3 done`，NOTIFY B |
| 3 | A1 | 已有代码；补租户隔离验证 | T-A1-01～05 | 全 PASS → `A1 done`，NOTIFY B |
| 4 | A2 | 已有代码；确认四表 CRUD + 租户隔离 | T-A2-01～06 | 全 PASS → `A2 done`，NOTIFY B |
| 5 | A4 | **需新建**；Faiss per-tenant add/search/delete | T-A4-01～03 | 全 PASS → `A4 done`，NOTIFY B |
| 并行 | fixture | 已交付四文件；A5/A7/A8 完成后刷新 | — | — |

```text
【NOTIFY · 请通知开发者 B】（A0/A1/A2/A3 完成后发送）
底座已就绪：IndustryPack(A0) · JWT+租户(A1) · KB CRUD(A2) · LLM Gateway(A3)。
你可开始/继续：B1（调 chat）· B3（kb_fetch + fact_refs）· B4（禁词）。
请确认请求头带 Authorization: Bearer <JWT>。
```

---

*开发者 A 手册 v1.0 · 逐步测试强制验收 · 进度以 G-L3-开发进度.md 为准*
