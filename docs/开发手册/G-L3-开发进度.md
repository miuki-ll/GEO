# GEO 开发进度表（双人同步）

> **版本**：v1.3 | **日期**：2026-07-16  
> **用途**：两人通过 **git 提交本文件** 同步进度；Agent / 人开工前先读此表。  
> **A / B 各自开工前请同时阅读自己的专用手册。**  
> **任务定义与依赖**：见 [G-L3-双人任务拆分.md](G-L3-双人任务拆分.md)（WAIT_FOR / NOTIFY / GATE）  
> **开发者 A 专用手册**：[G-L3-开发者A任务手册.md](G-L3-开发者A任务手册.md)（**§11 测试强制验收**）  
> **开发者 B 专用手册**：[G-L3-开发者B任务手册.md](G-L3-开发者B任务手册.md)（§3 顺序阻塞 · **§11 测试强制验收**）  
> **实施细则**：见 [G-L3-实施清单.md](G-L3-实施清单.md)

---

## 0. 同步约定（git）

| 规则 | 说明 |
|------|------|
| **只改自己的行** | A 只改「开发者 A」表与本人相关 GATE 备注；B 同理。避免同单元格冲突 |
| **状态变更即提交** | 任务开始 / 完成 / 阻塞时立刻改本文件并 `git commit` + `git push` |
| **Commit 消息格式** | `progress: A7 done` / `progress: B1 blocked WAIT_FOR A8` / `progress: G2 green` |
| **拉最新再改** | 改进度前先 `git pull`，减少合并冲突 |
| **阻塞必填** | 状态为 `blocked` 时，`阻塞原因` 列必须写清 `WAIT_FOR: Ax/Bx` + 缺什么 |
| **完成必填** | 状态为 `done` 时，填 `完成日`；若有 NOTIFY，在备注写「已通知对方」 |
| **A 轨测试强制** | 开发者 A 标 `done` 前必须按 [G-L3-开发者A任务手册.md](G-L3-开发者A任务手册.md) **§11** 跑通对应用例；备注写 `tests: Ax pass`（或失败用例 ID）。**未测/失败不得 done** |
| **B 轨测试强制** | 开发者 B 标 `done` 前必须按 [G-L3-开发者B任务手册.md](G-L3-开发者B任务手册.md) **§11** 跑通对应用例；备注写 `tests: Bx pass`（或失败用例 ID）。**未测/失败不得 done** |

### 状态枚举（勿自创）

| 值 | 含义 |
|----|------|
| `todo` | 未开始 |
| `doing` | 进行中（含写测试中） |
| `blocked` | 被对方或外部阻塞，或**测试失败待修**（须填阻塞原因） |
| `done` | 已完成且可被对方依赖；**B 轨还须 §11 测试全 PASS** |
| `skip` | MVP 明确不做（须备注原因） |

### 当前冲刺摘要（每次改进度时顺手更新）

| 项 | 值 |
|----|-----|
| **更新日期** | 2026-07-17 |
| **当前周** | W1 |
| **A 当前任务** | A2（KB CRUD）准备中 |
| **B 当前任务** | B0（可 MOCK 先行）· **G1 可验** |
| **全局阻塞** | **B1 真接 WAIT_FOR A7+A8**；**G4 WAIT_FOR A7**；B5 AUTO WAIT_FOR A5；**A0 已 done → B4 可接禁词** |
| **下一联调 GATE** | G1（信封+JWT）✅ 可验；G2/G4 暂不可绿 |
| **备注** | A0+A1 已通知 B；详见 B 手册 §3.1–§3.3 · **§11 测试**；SEMI/B2 可先做 |

---

## 1. 开发者 A · 上游进度

| ID | 任务 | 状态 | 开始日 | 完成日 | 阻塞原因（WAIT_FOR） | 备注 / 交付物 |
|----|------|------|--------|--------|----------------------|---------------|
| A0 | IndustryPack 基类 + beauty_local 规则簿 | `done` | 2026-07-17 | 2026-07-17 | | tests: A0 pass · 已通知 B → B4/B1 |
| A1 | 注册/登录/JWT/RBAC/租户隔离 | `done` | 2026-07-17 | 2026-07-17 | | tests: A1 pass · 已通知 B → G1 |
| A2 | KB CRUD（Fact/FAQ/Signal） | `todo` | | | | NOTIFY B → fact_refs |
| A3 | LLM Gateway × 4 Adapter | `done` | 2026-07-19 | 2026-07-19 | | tests: A3 pass · 已通知 B → B1/B3 |
| A4 | Faiss per-tenant | `todo` | | | | |
| A5 | 开店向导：建库 + Schema + llms.txt | `todo` | | | | |
| A6 | onboarding SSE 进度 | `todo` | | | | |
| A7 | 诊断 5 项 + 写 T0 | `todo` | | | | NOTIFY B → B1/B6 |
| A8 | 四源汇聚词库 + CRUD | `todo` | | | | NOTIFY B → B1 |
| A9 | 前端：登录/入驻/KB/设置（主攻 AI） | `todo` | | | 验 AC-13 时 `WAIT_FOR B6` | |

**A 过线（§2.4）**：入驻→SSE→健康报告→词库可编辑→T0→可改 `target_engines`  
**A 过线状态**：`todo`

**交接 fixture**（`backend/tests/fixtures/handoff_a_to_b/`）：

| 文件 | 状态 | 更新日 | 备注 |
|------|------|--------|------|
| enterprise.json | `done` | 7.16 |都是硬编码 |
| diagnosis.json | `done` | 7.16 | |    
| keywords.json | `done` | 7.16 | |
| kb_facts.json | `done` | 7.16 | |

---

## 2. 开发者 B · 下游进度

> 任务细节、I/O、WAIT_FOR、**逐步测试**见 **[G-L3-开发者B任务手册.md](G-L3-开发者B任务手册.md)**（§11）。状态只在本表更新。  
> **标 `done` 前：** 备注必须含 `tests: B<n> pass`；仅 MOCK 验收写 `tests: B<n> MOCK pass`。

| ID | 任务 | 状态 | 开始日 | 完成日 | 阻塞原因（WAIT_FOR） | 备注 / 交付物 / 测试 |
|----|------|------|--------|--------|----------------------|----------------------|
| B0 | 方案包/草稿页骨架（fixture mock） | `todo` | | | 缺 fixture 时 `WAIT_FOR A-fixture` · MOCK_OK | 验收：T-B0-01～04 |
| B1 | 方案包：persona/scenario/权重 0.6+0.4 | `todo` | | | 真接 `WAIT_FOR A7+A8`；另 A3/A0 · MOCK_OK | 验收：T-B1-01～06（真接加 R01/R02） |
| B2 | strategy-pack confirm | `todo` | | | | 验收：T-B2-01～05 |
| B3 | 内容工厂 + RAG 切片 | `todo` | | | 真接 `WAIT_FOR A2+A3` · MOCK_OK | 见手册 §11.4 |
| B4 | 5 项机审 + 人闸门 + approval_log | `todo` | | | `WAIT_FOR A0` 禁词/合规 | 见手册 §11.4 |
| B5 | 发布 AUTO + 小红书 SEMI | `todo` | | | 真发托管页 `WAIT_FOR A5` | SEMI 可先测；AUTO 另测 |
| B6 | Core/Probe + T1 + T0/T1 Δ + Engine 联动 | `todo` | | | `WAIT_FOR A7`（T0）；验 AC-13 时 `WAIT_FOR A9` | 见手册 §11.4 |
| B7 | 效果舱 Dashboard | `todo` | | | `WAIT_FOR A7`（T0 KPI） | 见手册 §11.4 |
| B8 | 前端：方案包/草稿/发布/监测/效果舱 | `todo` | | | 真接继承上表 | 见手册 §11.2 |

**B 过线**：勾选 scenario→机审→人闸门→AUTO+SEMI→效果舱见 Δ（详见 B 手册 §9）；**相关 Bx §11 测试均 PASS**  
**B 过线状态**：`todo`

---

## 3. 联调 GATE 进度

| GATE | 名称 | 需要 A | 需要 B | 状态 | 通过日 | 阻塞 / 备注 |
|------|------|--------|--------|------|--------|-------------|
| G1 | 信封 + JWT | A1 | B 受保护 API 可鉴权 | `ready` | | NOTIFY B 已发：B 带 JWT 调 GET /user/enterprise/profile 应 200 |
| G2 | 诊断 → 方案包 | A7+A8 真数据 | B1 读真 API | `todo` | | 约 W4 |
| G3 | 闸门 → 发布 | A0+A5 | B4+B5 | `todo` | | 约 W6 |
| G4 | T0/T1 Δ | A7 T0 | B5+B6 T1 | `todo` | | 约 W6 |
| G5 | AC-01 全链路 | A 过线 | B 过线 | `todo` | | 约 W8 |

---

## 4. AC 验收勾选（合并后勾）

| AC | 内容 | 状态 | 负责侧重 | 通过日 |
|----|------|------|----------|--------|
| AC-01 | 8 步流程跑通 | `todo` | 双方 G5 | |
| AC-02 | fact_refs 可追溯 | `todo` | A2+B3 | |
| AC-03 | 禁词拦截 | `todo` | A0+B4 | |
| AC-04 | 探针 LLM 生成 | `todo` | A7 | |
| AC-05 | 四层词库租户隔离 | `todo` | A8 | |
| AC-06 | persona LLM 生成 | `todo` | B1 | |
| AC-07 | scenario LLM 生成 | `todo` | B1 | |
| AC-08 | 渠道权重 0.6+0.4 | `todo` | B1 | |
| AC-09 | RAG 切片双步 | `todo` | B3+B4 | |
| AC-10 | 5 项机审 | `todo` | B4 | |
| AC-11 | 人闸门合并 | `todo` | B4 | |
| AC-12 | T0/T1 对比 | `todo` | A7+B6 | |
| AC-13 | 主攻 AI 联动 | `todo` | A9+B6 | |
| AC-14 | 租户隔离 403 | `todo` | A1 | |
| AC-15 | 行业包薄配置 | `todo` | A0 | |

---

## 5. 周进度快照（可选，每周五更新一行）

| 周 | 结束日 | A 完成项 | B 完成项 | GATE | 风险 |
|:--:|--------|---------|---------|------|------|
| W1 | | | | G1? | |
| W2 | | | | | |
| W3 | | | | | |
| W4 | | | | G2? | |
| W5 | | | | | |
| W6 | | | | G3/G4? | |
| W7 | | | | | |
| W8 | | | | G5? | |

---

## 6. Agent / 开发者更新本表流程

```text
1. git pull
2. 打开本文，改「当前冲刺摘要」+ 自己的任务行状态
3. 若 blocked：填 WAIT_FOR + 缺交付物；并按《双人任务拆分》复制提示话术通知对方
4. 若 done 且有 NOTIFY：备注写「已通知对方可开始 Bx/Ax」
5. git add docs/G-L3-开发进度.md
6. git commit -m "progress: <ID> <todo|doing|blocked|done> [WAIT_FOR ...]"
7. git push
```

**Agent 规则：**

- 开始某 `Ax`/`Bx` 前：读本表该行；若对方前置为非 `done` 且本任务有 `WAIT_FOR`，先提示对方，再决定 MOCK_OK 或暂停。
- 将任务标为 `done` 前：对照验收标准；**B 轨必须 §11 测试全 PASS**，备注写 `tests: Bx pass`。
- **不要**把对方轨任务改成 `done`。
- 宣称 GATE / AC 通过前：确认本表对应行为 `done` 且测试记录齐全。
- **A 轨 `done` 须手册 §11 测试 PASS；** 备注必须含 `tests: A<n> pass`。

---

## 7. 统计（自动心算用）

| 轨 | todo | doing | blocked | done | 合计 |
|----|:----:|:-----:|:-------:|:----:|:----:|
| A（A0–A9） | 6 | 0 | 0 | 3 | 10 |
| B（B0–B8） | 9 | 0 | 0 | 0 | 9 |
| GATE（G1–G5） | 5 | 0 | 0 | 0 | 5 |
| AC（01–15） | 15 | 0 | 0 | 0 | 15 |

> 改状态后请同步更新本统计数字，便于一眼看进度。

---

*G-L3-开发进度表 v1.2 · B 轨 done 须手册 §11 测试通过 · 以 git 为本同步源*
