# GEO · 开发者 B 轨技术债（B0–B5 结算）

> **版本**：v1.4 | **日期**：2026-07-17  
> **触发点**：B5 MOCK 主链交付后结算；进 B6 前须知账，不挡 SEMI 手验  
> **依据**： [G-L3-开发者B任务手册.md](G-L3-开发者B任务手册.md) §11 · [G-L3-API契约.md](G-L3-API契约.md) · 2026-07-17 合规抽检  
> **进度表**： [G-L3-开发进度.md](G-L3-开发进度.md)（本文件只记账，不替代进度行状态）

---

## 0. 怎么用

| 规则 | 说明 |
|------|------|
| **不挡 MOCK 前进** | 下列债不阻止 B5 SEMI 手验 / 开 B6 壳；但 **不得** 拿「MOCK done」冒充 GATE / 真接 done |
| **还债时机** | P0 建议 B6 开工前或并行第一周还清；P1 联调 G1/G2 前；P2 可排 W5–W7 |
| **勾选** | 还清后把「状态」改为 `done`，并在进度表对应 Bx 备注补一行 `debt: TD-xxx cleared` |
| **不记什么** | A 侧未交付（WAIT_FOR A0/A5/A7…）记在进度表阻塞列，**不**算作 B 技术债 |

### 状态枚举

`open` · `doing` · `done` · `wontfix`（须备注原因）

---

## 1. 总览

| ID | 优先级 | 标题 | 来源阶段 | 建议还债窗口 | 状态 |
|----|:------:|------|:--------:|--------------|:----:|
| TD-01 | **P0** | §11 测试弱断言，done 声明过满 | B2/B5 | B6 前 | `done` |
| TD-02 | **P0** | pytest 无 `pythonpath`，默认跑挂 | B0–B5 | 立刻 | `done` |
| TD-03 | **P1** | 信封字段 `msg` vs `message` | 共建契约 | G1 前 | `open` |
| TD-04 | **P1** | `forbidden_words` 布尔语义与手册示例相反 | B4 | G3 / AC-03 前 | `done` |
| TD-05 | **P2** | 发布模式大小写 `AUTO` vs `auto` | B5 | 契约终态时 | `open` |
| TD-06 | **P2** | 草稿状态多了 `approved` | B4/B8 | 契约终态时 | `open` |
| TD-07 | **P2** | 禁词兜底硬编码灰区 | B4 | A0 真接时删 | `open` |
| TD-08 | **P2** | B8 监测/效果舱仍为前端假数据 | B8 | 跟 B6/B7 | `open` |
| TD-09 | **P1** | B0–B1 手测清单未落盘 | B0/B1 | 补记录即可 | `open` |
| TD-10 | **P0** | `monitor_results` 无 `baseline`，无法区分 T0/T1 | B6 前置 | B6 开工时 | `done` |
| TD-11 | **P2** | 方案包页缺 `TODO(WAIT_FOR: A7+A8)`；scenario 勾选未硬限 5 | B1/B8 | 真接前 | `done` |
| TD-12 | **P2** | monitor/outcomes 假数据无 MOCK 黄条；`ops.ts` 已有客户端未接线 | B8 | 跟 B6/B7 | `open` |

---

## 2. 分条说明

### TD-01 · §11 测试弱断言（P0）

**现象**

- `tests/b_track/test_b2_confirm.py`：未打真实 `POST /strategy-pack/confirm`，未验 DB 落库 / Job / 超 max 4xx / 跨租户 403；存在「`len(selected)>5` 字面量」「`next_route` 字符串常量」类空断言。
- `tests/b_track/test_b5_publish.py` 中 `test_tb5_run_payload_shape`：手工构造 `{started:2}` 再 assert，未调 `POST /publish/run`。
- 进度表写 `tests: B2 pass` / 部分 `tests: Bx pass`，对照手册 §11.3–§11.4 **过满**。

**还债标准**

| 任务 | 最低补测 |
|------|----------|
| B2 | T-B2-01～05：HTTP confirm · scenarios 落库 · content 触达 · 未选/超 5 → 4xx · 跨租户不可读 |
| B5 | 真实 `POST /publish/run` → `started`；SEMI 五字段经 API 回读；AUTO mock URL 字段存在 |

**建议处置（进度口径）**

- 未补测前：B2 备注改为 `tests: B2 partial（缺 API/DB/403）`；B5 保持 `doing` / `tests: B5 MOCK partial` 亦可。
- 补测全 PASS 后再写回 `tests: Bx pass`。

**涉及路径**：`backend/tests/b_track/test_b2_*.py` · `test_b5_*.py` ·（可选）TestClient 夹具

---

### TD-02 · pytest 默认无法 import `app`（P0）

**现象**

```text
pytest tests/b_track/ -q
→ ModuleNotFoundError: No module named 'app'
```

需手动 `PYTHONPATH=backend`（或等价）才 **25 passed**。仓库无 `pytest.ini` / `pyproject.toml` 的 `pythonpath`。

**还债标准**

- 在 `backend/` 增加 `pytest.ini`（或 `pyproject.toml`）：`pythonpath = .`
- 文档命令与手册 §11.1 一致：`cd backend && pytest tests/b_track/… -q` 零额外环境变量即可绿。

---

### TD-03 · 统一信封 `msg` vs `message`（P1 · 共建）

**现象**

| 来源 | 字段 |
|------|------|
| API 契约 / B 手册 | `msg` |
| `app/schemas/common.py` · 前端 `request.ts` | `message` |

**还债标准**

- 契约与实现二选一对齐（建议：**实现跟契约改 `msg`**，或契约显式改名为 `message` 并全仓替换）。
- 前端拦截器与错误提示同步。
- **PR 双方 review**（手册写明共建）。

**阻塞**：G1 信封验收。

---

### TD-04 · `machine_review.forbidden_words` 语义（P1）

**现象**

- 手册示例 ready 稿：`forbidden_words: false` 表示「未命中禁词 / 通过」。
- 实现 `content_review.run_five_machine_reviews`：`forbidden_words: True` 表示通过（与其余四键同向）。
- 注释已写明手册语义，实现仍取反；前端按「truthy=绿」渲染。

**还债标准**

1. 与契约/手册定稿一种语义（推荐：五键统一 **true=该项通过**，并改手册示例；或严格跟手册示例，则前端/聚合 `all()` 逻辑要特殊处理禁词键）。
2. 更新 `test_b4_review.py` + 草稿预览展示文案。
3. 进度备注写清最终语义，避免联调各说各话。

---

### TD-05 · 发布 `mode` 大小写（P2）

**现象**：手册 `AUTO | SEMI | GUIDED`；DB/服务默认 `auto | semi | guided`。

**还债标准**：契约终态定一种；API 出参可统一大写、入库小写，或文档改为小写枚举。前端展示已做 `toUpperCase`，兼容但契约仍欠清。

---

### TD-06 · 草稿状态多 `approved`（P2）

**现象**：手册枚举 `draft | ready | published | rejected`；前端筛选含 `approved`，人审通过路径可能写入扩展状态。

**还债标准**：要么写入契约扩展枚举，要么人审后仍用 `ready`/`published` 并去掉 UI 多余档。

---

### TD-07 · 禁词兜底硬编码（P2）

**现象**：`content_review.resolve_forbidden_words` 在 IndustryPack 失败时回落 `["根治","永不复发","100%有效","国家级"]`。不在 `content_service` 内，但仍属「永久副本」灰区。

**还债标准**：A0 真接后删除兜底或仅 `APP_ENV=test` 可见；业务路径只走 `get_industry_pack(...).forbidden_words()`。

**关联**：进度 B4 `WAIT_FOR A0`。

---

### TD-08 · B8 监测 / 效果舱假数据（P2 · 已知未做）

**现象**

- `frontend/src/views/monitor/Index.vue`：硬编码表格；按钮 toast「S5 阶段实现」。
- `frontend/src/views/outcomes/Index.vue`：假 KPI / 图，未调 `GET …/outcomes/dashboard`。

**还债标准**：跟 B6/B7 一并接线；不得单独把 B8 标满 done。进度表已写「监测/效果舱未做」——**债在账、状态已诚实**。

---

### TD-09 · B0/B1 手测未落盘（P1）

**现象**：§11.3 T-B0-01/02、T-B1-05 为手测；仓库仅有 schema/公式单测，无勾选记录。

**还债标准**：在本文件或 PR 描述贴一份勾选（日期 + 操作人），例如：

```text
T-B0-01 /strategy-pack 五区  PASS  2026-07-17
T-B0-02 /content/drafts      PASS  …
T-B1-05 五区渲染无致命错误   PASS  …
```

---

### TD-10 · 监测缺 `baseline` 字段（P0 · B6 前置）

**现象**：全仓无 `baseline` 字段/列。手册 B6 约定 `baseline: true` = T0（A 写）、`false` = T1（B 写）；缺此则无法算 Δ / 过 G4。

**还债标准**

- Alembic：`monitor_results.baseline`（Boolean，默认 `false`）
- 写入/查询 API 与 `DashboardService` 按 baseline 聚合 `mention_rate_t0/t1`
- 与 A7 T0 写入约定对齐（A 写 baseline=true；B 写 T1）

**涉及**：`models` / Alembic（共建）· `monitor_service` · `dashboard_service` · B6 测试

---

### TD-11 · 方案包前端真接标记与勾选硬限（P2）

**现象**（前端审计）

- `/strategy-pack` 无 `TODO(WAIT_FOR: A7+A8)`（B1 清单要求真接切换点有标注）；草稿/发布页已有同类 TODO。
- Scenario 勾选：UI 文案「最多 5」，confirm 时 `slice(0,5)`，表格未禁止勾第 6 项（易误解）。

**还债标准**：补 WAIT_FOR 注释或黄条；勾选 >5 时禁用多余行或即时提示。

---

### TD-12 · 监测/效果舱未接线 + 无 MOCK 标识（P2）

**现象**：`ops.ts` 已有 `listCore` / `listProbe` / `getDashboard` 等，views 未用；假数据也无 MOCK/WAIT_FOR 提示（比方案包页更易误当真数据）。与 TD-08 同源，单列便于勾选。

**还债标准**：接线或至少加「演示数据」条；B6/B7 完成时关闭 TD-08+TD-12。

---

## 3. 明确「不是技术债」（等 A）

下列写在进度表 WAIT_FOR，**不要**混进本债表当 B 欠账：

| 依赖 | 影响 |
|------|------|
| A-fixture 官方四文件 | B0 交接完成态 |
| A7+A8（+A3/A0） | B1 真接 / G2 |
| A2+A3 | B3 真 fact_refs / chat |
| A0 IndustryPack | B4 禁词正式路径 / AC-03 |
| A5 托管页 | B5 AUTO 真发 |
| A7 T0 | B6/B7 Δ / G4 |
| A1 JWT + 登录真接 | G1 |

---

## 4. 建议还债顺序（进 B6 前）

```text
1. TD-02  pytest.ini          （半小时级）
2. TD-01  补 B2/B5 真 API 测   （0.5–1 天；同时校正进度备注）
3. TD-09  手测勾选落盘         （跟手验一起）
4. TD-10  baseline 列（B6 第一刀，与 A7 约定）
5. TD-03 / TD-04  与 A 对齐契约（联调周）
6. TD-05 / TD-06 / TD-07       （契约终态或 A0 到时）
7. TD-08 / TD-12             （B6/B7 自然消化）
```

---

## 5. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-07-17 | v1.0 初版：B5 MOCK 结算，自合规抽检录入 TD-01～09 |
| 2026-07-17 | v1.1 补 TD-10：后端审计确认无 `baseline` |
| 2026-07-17 | v1.2 补 TD-11/12：前端审计（WAIT_FOR 标记、monitor/outcomes 未接线） |
| 2026-07-17 | v1.3 还清 TD-02/01/11/10：`pytest.ini` · B2/B5 service 测 · 方案包硬限5 · `baseline` 列+迁移 |
| 2026-07-17 | v1.4 还清 TD-04：五键统一 true=通过；契约/B 手册/拆分示例已改；补极性单测 |

---

*G-L3-B轨技术债 v1.0 · 与进度表并行维护 · 还清请改状态并 progress commit*
