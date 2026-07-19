# 开发者 A · 实施 TODO

>> **版本**：v2.1 | **日期**：2026-07-17
> **图例**：⬜ todo 🟦 doing 🟩 done 🔴 blocked ⚠️ 需新建 🔍 审查者验收（无 step，由 Claude 执行）

---

## W1：底座（A0–A4 + fixture）

---

### A0 · IndustryPack 基类 + beauty_local 规则簿
> **现状态**：代码已有，6 方法抽象 + beauty_local 实现 + templates 全
> **涉及文件**（只读验证，不改代码）：

| 文件 | 作用 |
|------|------|
| `backend/app/agents/industry/base.py` | IndustryPack ABC — 6 个抽象方法 |
| `backend/app/agents/industry/registry.py` | get_industry_pack() 注册表 |
| `backend/app/agents/industry/packs/beauty_local/pack.py` | BeautyLocalPack 实现 |
| `backend/app/agents/industry/packs/beauty_local/templates.py` | 禁词/渠道权重/默认画像/fact模板/scenario模板/合规清单 |
| `backend/app/agents/industry/packs/beauty_local/seed.py` | 种子数据 |

- [x] **[A0-1](./steps/A0-1.md)** — 核实基类 6 个抽象方法 + templates() 聚合方法
- [x] **[A0-2](./steps/A0-2.md)** — 核实 pack.py 的 code/name + 6 方法委托 + registry 注册
- [x] **[A0-3](./steps/A0-3.md)** — 检查 templates.py 7 个常量数据完整性（禁词≥10/渠道5/竞品≥3/合规≥3）
- [x] **[A0-4](./steps/A0-4.md)** — ⚠️ 新建 `test_a0_industry_pack.py`，6 条用例全 PASS
- [x] **[A0-5](./steps/A0-5.md)** — 验收：更新进度表 + git push + 发 NOTIFY B

---

### A1 · 注册/登录/JWT/RBAC/租户隔离
> **现状态**：代码已有，需 3 处改动 + 验证 + 前端对接
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/api/v1/auth.py` | register/login 路由 | 🛠️ 合并登录端点 |
| `backend/app/core/security.py` | JWT 签发/校验 + get_current_user | 🟢 不改 |
| `backend/app/service/auth_service.py` | EnterpriseService + UserService | 🛠️ 加重名检查 |
| `backend/app/schemas/auth.py` | UserCreate/Login/TokenPayload | 🟢 不改 |
| `backend/app/models/auth.py` | Enterprise / User / RolePermission | 🛠️ name 加 unique |
| `frontend/src/views/Login.vue` | 登录页 | 🛠️ 切真实 API |
| `frontend/src/views/Register.vue` | 注册页 | 🛠️ 切真实 API |

- [x] **[A1-1](./steps/A1-1.md)** — 🛠️ 合并登录端点为 JSON only + Enterprise.name 唯一约束
- [x] **[A1-2](./steps/A1-2.md)** — 🛠️ Login.vue / Register.vue 切真实 API
- [x] **[A1-3](./steps/A1-3.md)** — 🔍 全链路验证：register → login → JWT → 租户隔离 → target_engines
- [x] **[A1-4](./steps/A1-4.md)** — 🆕 新建 `test_a1_auth.py`，6 条用例全 PASS
- [x] **🔍 A1 验收（审查者）** — ✅ 审查通过（2026-07-17）：6 tests pass + git diff 文件在清单内 + 无越权改动。已 NOTIFY B → G1

---

### A2 · KB CRUD（Fact/FAQ/Signal/External）
> **现状态**：代码已有，kb.py 246 行 + kb_service.py 完整
> **涉及文件**：

| 文件 | 作用 |
|------|------|
| `backend/app/api/v1/user/kb.py` | 四表 CRUD 路由 + summary |
| `backend/app/service/kb_service.py` | FactService/FaqService/SignalService/ExternalService/KBSummaryService |
| `backend/app/models/kb.py` | KBFact / KBFaq / KBSignal / KBExternal |
| `backend/app/schemas/kb.py` | Request/Response schema |
| `backend/app/service/kb_freshness_service.py` | kb_freshness + thin_kb_check |

- [x] **[A2-1](./steps/A2-1.md)** — 🔍 核实 kb_facts 7 端点 — CRUD + 分页 + 租户注入 + 角色控制
- [x] **[A2-2](./steps/A2-2.md)** — 🔍 核实 kb_faqs / kb_signals / kb_externals — 复用 _BaseKBService
- [x] **[A2-3](./steps/A2-3.md)** — 🔍 核实 KB Summary 聚合 + kb_freshness + thin_kb_check
- [x] **[A2-4](./steps/A2-4.md)** — 🧪 新建 `test_a2_kb.py`，8 条用例全 PASS（6 API + 2 Service）
- [x] **🔍 A2 验收（审查者）** — ✅ 审查通过（2026-07-19）：26 tests pass + 仅新建 test_a2_kb.py + 无越权改动。已 NOTIFY B

---

### A3 · LLM Gateway × 4 EngineAdapter
> **现状态**：代码已有，gateway.py 173 行 + adapters.py 完整。联网搜索已验证通过。
> **已验证**：
> - ✅ Chat API：`doubao-seed-2-1-pro-260628` 可用（ep-20260717201633-hknqf 也行）
> - ✅ Responses API + web_search：**直接用模型名** `doubao-seed-2-1-pro-260628`，不能用 ep-xxx
> - ✅ citations 解析：`output[].content[].annotations[type=url_citation]`，含 title/url/summary(1200+字)/site_name/publish_time
> - ✅ summary 足够做痛点/场景/竞品分析，不需要额外爬全文
> - ✅ timeout 需 ≥180s，API Key 已写入 `.env`
> - 📄 接入文档：[豆包.md](../../../豆包.md) · 测试脚本：[test_doubao.py](../../../backend/test_doubao.py)
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/core/llm/gateway.py` | LLMGateway — chat()/embed()/search() 统一入口 | 🛠️ 需加 search() |
| `backend/app/core/llm/adapters.py` | DoubaoAdapter / DeepseekAdapter / KimiAdapter / WenxinAdapter | 🛠️ DoubaoAdapter 需加 search() |
| `backend/app/core/llm/base.py` | BaseEngineAdapter 抽象类 | 🛠️ 需加 search() 可选方法 |
| `backend/app/core/llm/schemas.py` | LLMRequest / LLMResponse / SearchRequest / SearchResponse | 🛠️ 需加 SearchRequest/SearchResponse/SearchCitation |
| `backend/app/core/config.py` | API keys / base URLs | 🟢 已有 DOUBAO_API_KEY |

- [x] **[A3-1](./steps/A3-1.md)** — 🛠️ schemas 加 SearchCitation/SearchRequest/SearchResponse + base 加 search() 可选方法
- [x] **[A3-2](./steps/A3-2.md)** — 🛠️ DoubaoAdapter.search() + gateway.search() + `__init__.py` 导出
- [x] **[A3-3](./steps/A3-3.md)** — 🔍 核实 4 Adapter 注册/降级/embed/重试（只读验证）
- [x] **[A3-4](./steps/A3-4.md)** — 🧪 新建 `test_a3_gateway.py`，T-A3-01~06 全 PASS（含 search mock）
- [x] **🔍 A3 验收（审查者）** — ✅ 审查通过（2026-07-19）：18 tests pass + git diff 文件在清单内 + 无越权改动。已 NOTIFY B

### ✅ 已确定事项（2026-07-19）

| # | 问题 | 决策 |
|---|------|------|
| 1 | 并发方案（A7 25条探针慢） | **B+C 并行**：Celery 任务队列 + BackgroundTasks/SSE 进度推送 |
| 2 | 持久化方案（citations 存哪里） | **方案 B**：新建 `search_results` 独立表 |
| 3 | 非豆包引擎的 search() | gateway.search() 自动降级到 chat 模拟，标记 `simulated=true` |
| 4 | DeepSeek/Kimi/文心 的 API Key | 待用户提供（仅影响降级链，不阻塞 A3-A7） |

---

### A4 · Faiss per-tenant 向量库 ⚠️ 需新建
> **方案**：磁盘持久化（`faiss.write_index` / `faiss.read_index`）+ 方案 C（dirty 标记 + Celery 异步逐条同步）
> **模型**：bge-small-zh-v1.5（384 维），路径放 `.env`
> **现状态**：`FaissIndex` model 在 `models/ops.py`，`rag/__init__.py` 空壳，embedding 在 `core/embedding.py`
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/models/ops.py` | FaissIndex 表定义 | 🟢 已有 |
| `backend/app/core/embedding.py` | get_embedding_function() — 改为从 settings 读路径 | 🛠️ 待改 |
| `backend/app/core/config.py` | 新增 EMBEDDING_MODEL_PATH | 🛠️ 待改 |
| `backend/.env` | 新增 EMBEDDING_MODEL_PATH | 🛠️ 待改 |
| `backend/app/rag/__init__.py` | 空壳 → 导出 FaissService | 🛠️ 待改 |
| `backend/app/rag/faiss_service.py` | Faiss per-tenant add/search/delete/rebuild + 磁盘持久化 | 🔴 待建 |
| `backend/app/tasks/faiss_tasks.py` | Celery 异步任务（sync_item / rebuild_index） | 🔴 待建 |
| `backend/app/tasks/__init__.py` | 注册 faiss_tasks | 🛠️ 待改 |
| `backend/app/service/kb_service.py` | _create/_update/_delete 接 Celery 触发 | 🛠️ 待改 |

- [x] **[A4-1](./steps/A4-1.md)** — 🆕 新建 `faiss_service.py` + `faiss_tasks.py` + config/.env/embedding 适配
- [x] **[A4-2](./steps/A4-2.md)** — 🛠️ 接线：kb_service 增删改 → Celery 任务 + `rag/__init__.py` 导出
- [x] **[A4-3](./steps/A4-3.md)** — 🧪 新建 `test_a4_faiss.py`，3 条用例（mock embedding）
- [x] **🔍 A4 验收（审查者）** — ✅ 审查通过（2026-07-19）：一次驳回 A4-3（ImportError），修复后二次验收 29 passed。

---

### 📦 Fixture 交接包
> **现状态**：✅ 四文件已交付
> **涉及目录**：`backend/tests/fixtures/handoff_a_to_b/`

- [x] **FIX-1** — `backend/tests/fixtures/handoff_a_to_b/enterprise.json` — ✅ 已交付
- [x] **FIX-2** — `backend/tests/fixtures/handoff_a_to_b/diagnosis.json` — ✅ 已交付
- [x] **FIX-3** — `backend/tests/fixtures/handoff_a_to_b/keywords.json` — ✅ 已交付
- [x] **FIX-4** — `backend/tests/fixtures/handoff_a_to_b/kb_facts.json` — ✅ 已交付
- [ ] **FIX-5** — 后续：A5/A7/A8 完成后按真实 schema 刷新 fixture 四文件

---

## W2：入驻（A5–A6）

---

### A5 · 开店向导 API ⚠️ 骨架已有，逻辑需实现
> **方案**：走 graph 系统（nodes.py）+ /run 一次性接收全部表单 + 4 节点顺序 LLM + 并行 search 兜底
> **现状态**：`/onboarding/run` 路由存在，`nodes.py` 空壳，`diagnosis_service.py` 硬编码
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/api/v1/user/onboarding.py` | POST /run 路由 + GET /status | 🟡 骨架 |
| `backend/app/agents/graphs/onboarding/graph.py` | 注册 onboarding_graph | 🟡 骨架 |
| `backend/app/agents/graphs/onboarding/nodes.py` | 4 节点实现（**空壳**） | 🔴 需重写 |
| `backend/app/agents/graphs/onboarding/edges.py` | 节点间路由逻辑 | 🟡 待确认 |
| `backend/app/agents/graphs/onboarding/state.py` | AgentGraphState 定义 | 🟡 待确认 |
| `backend/app/agents/registry.py` | register_graph | 🟢 已有 |
| `backend/app/agents/runner.py` | Agent 执行器 | 🟢 已有 |
| `backend/app/service/agent_task_service.py` | AgentTask CRUD + progress | 🟢 已有 |
| `backend/app/models/strategy.py` | AgentTask / TargetEngine model | 🟢 已有 |
| `backend/app/models/auth.py` | Brand / Store / Service / Enterprise model | 🟢 已有 |
| `backend/app/models/kb.py` | KBFact / KBSignal model | 🟢 已有 |
| `backend/app/schemas/business.py` | AgentTaskCreate / AgentTaskResponse | 🟢 已有 |
| `backend/app/schemas/agent.py` | Agent 相关 schema | 🟢 已有 |
| `backend/app/service/kb_freshness_service.py` | thin_kb_check | 🟢 已有 |

- [ ] **[A5-1](./steps/A5-1.md)** — 🛠️ 重写 `nodes.py`：4 个 LLM 节点（DIAGNOSE→PAIN→PERSONA→COMPETITOR）+ 并行 search 兜底
- [ ] **[A5-2](./steps/A5-2.md)** — 🛠️ `onboarding.py` 改造：新 `OnboardingRunRequest` schema + 切 `runner.run_graph()` + Brand/Store/Service 副作用写入
- [ ] **[A5-3](./steps/A5-3.md)** — 🛠️ KB 自动建库：seed_facts → KBFact/KBSignal + thin_kb_check + llms.txt 骨架
- [ ] **[A5-4](./steps/A5-4.md)** — 🧪 新建 `test_a5_onboarding.py`，6 条用例（mock LLM 全流程）

### A6 · onboarding SSE 进度
> **现状态**：`nodes.py` 空壳已有 progress_pct 赋值，但 SSE 端点需实现
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/api/v1/user/onboarding.py` | SSE 端点可加在此文件 | 🟡 待加 |
| `backend/app/service/agent_task_service.py` | update_progress / complete_task | 🟢 已有 |
| `backend/app/agents/graphs/onboarding/nodes.py` | 节点进度更新 | 🟡 待完善 |

- [ ] **A6-1** — `backend/app/api/v1/user/onboarding.py` — 新增 `GET /onboarding/status/{task_id}` SSE 端点
  - Content-Type: `text/event-stream`
  - 从 `agent_tasks` 轮询 `progress_pct` + `progress_message` + `status`
- [ ] **A6-2** — `backend/app/agents/graphs/onboarding/nodes.py` — 每个节点完成后调 `AgentTaskService.update_progress()` 更新进度（25%→50%→75%→100%）
- [ ] **A6-3** — `backend/app/service/agent_task_service.py` — `complete_task` 时写入 `next_route: "/strategy-pack?draft=1"` 到 output_data
- [ ] **A6-4** — `backend/app/api/v1/user/onboarding.py` — SSE 断线重连：客户端重连时从当前 `progress_pct` 继续推送
- [ ] **A6-5** — `backend/tests/a_track/test_a6_sse.py` — ⚠️ 新建，验证 SSE 递增到 100 + next_route
- [ ] **A6-6** — 验收：进度表 `A6 done`

---

## W3：诊断（A7）

---

### A7 · 诊断 5 项 + 写 T0 ⚠️ 部分已有，需补全
> **现状态**：`diagnosis.py` 有 pain/persona/competitor 三个 GET + `/all` POST，但 diagnosis_service 用随机默认数据，非 LLM 驱动
> **联网搜索方案**（2026-07-18 验证通过）：
> - Responses API + `web_search` tool → 每条探针约 2-3min，返回 9+ citations（每条 summary 1200+字）
> - citations → `source_diagnoses.payload` 持久化 → 喂 LLM 做痛点/场景/竞品分析
> - **详细文档**：[豆包.md](../../../豆包.md)
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/api/v1/user/diagnosis.py` | 诊断路由（pain/persona/competitor/all） | 🟡 部分 |
| `backend/app/service/diagnosis_service.py` | diagnose_probe/batch_search/build_source_map/analyze_competitors/write_t0 | 🟡 需重写 |
| `backend/app/models/strategy.py` | SourceDiagnosis / Keyword model | 🟢 已有 |
| `backend/app/models/monitor.py` | MonitorResult（T0 写入目标） | 🟢 已有 |
| `backend/app/schemas/diagnosis.py` | 诊断 response schema | 🟡 待补 SourceMap/Citation/SearchResult |
| `backend/app/schemas/business.py` | PersonaData / CompetitorItem / PainPoint | 🟡 待确认 |
| `backend/app/core/llm/gateway.py` | A3 gateway.chat() + gateway.search()（A3-3 新增） | 🟡 依赖 A3-3 |

- [ ] **A7-1** — 重写 `diagnose_probe()`：品类+商圈+店名→`gateway.chat()`→20-30条自然问句
- [ ] **A7-2** — 新增 `batch_search_engines()`：逐条探针调 `gateway.search()`（豆包联网搜索），记录 answer+citations，并发控制（QPS≤5）
- [ ] **A7-3** — 新增 `analyze_from_citations()`：从 citations[].summary + answer 调 `gateway.chat()`→brand_mentioned/rank/competitor_occupancy/pain_points/track
- [ ] **A7-4** — 新增 `build_source_map()`：从 citations 聚合 domain→count→weight→rankings+gaps
- [ ] **A7-5** — 新增 `write_t0_baseline()`：探针+answer+citations 全量写入 `monitor_results`，`metadata_json.baseline=true`
- [ ] **A7-6** — `GET /diagnosis/{id}` 返回完整五区 JSON（见下方设计）
- [ ] **A7-7** — `POST /diagnosis/all` 改为异步流水线：generate_probes→batch_search→analyze→build_map→write_t0，SSE 推进度
- [ ] **A7-8** — `backend/app/schemas/diagnosis.py` — 新增 Citation / SearchResult / SourceMap / DiagnosisFullResponse
- [ ] **A7-9** — `backend/tests/a_track/test_a7_diagnosis.py` — ⚠️ 新建
- [ ] **A7-10** — 验收：进度表 `A7 done`，发 **NOTIFY B（关键）**
- [ ] **A7-11** — `backend/tests/fixtures/handoff_a_to_b/diagnosis.json` — 按真实输出形状刷新

### 🟡 A7 待确定

| # | 问题 | 状态 |
|---|------|:--:|
| 1 | 25条探针×180s=75min 太慢，异步+并发怎么设计？ | 待讨论 |
| 2 | 非豆包引擎（DeepSeek/Kimi）没有联网搜索，诊断跳过还是模拟？ | 待定 |
| 3 | citations 的 summary 持久化到哪？`source_diagnoses.payload` 还是独立表？ | 倾向于 payload JSON |

---

## W4：词库（A8）

---

### A8 · 四源汇聚词库 + CRUD + generate ⚠️ 整模块缺失
> **现状态**：`keywords` 表在 `models/strategy.py`，但无独立路由/service/schema
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/models/strategy.py` | Keyword model | 🟢 已有 |
| `backend/app/api/v1/user/` | **keyword.py** — 路由 | 🔴 待建 |
| `backend/app/service/` | **keyword_service.py** — 服务 | 🔴 待建 |
| `backend/app/schemas/` | **keyword.py** — schema | 🔴 待建 |
| `backend/app/core/llm/gateway.py` | A3 gateway.chat() | 🟢 已有 |
| `backend/app/service/diagnosis_service.py` | A7 探针问句（来源之一） | 🟡 依赖 A7 |
| `backend/app/api/v1/user/onboarding.py` | raw_inputs（来源之一） | 🟡 依赖 A5 |
| `frontend/src/views/knowledge-base/Index.vue` | 词库前端 | 🟡 骨架 |
| `frontend/src/api/kb.ts` | KB API 封装 | 🟡 待加 keyword 接口 |

- [ ] **A8-1** — `backend/app/schemas/keyword.py` — ⚠️ 新建 schema 文件：
  - `KeywordCreate` / `KeywordUpdate` / `KeywordResponse` / `KeywordListParams`
  - layer 枚举：`认知层|选型层|痛点层|场景层`
  - source 枚举：`RawInputs|探针反推|SEO API|LLM生成|手动`
- [ ] **A8-2** — `backend/app/service/keyword_service.py` — ⚠️ 新建 service，实现四源汇聚逻辑：
  - `_from_raw_inputs(eid)` → 入驻 raw_inputs 拆词
  - `_from_probes(eid)` → A7 探针问句提取关键词
  - `_from_seo(eid)` → SEO API（MVP mock 假数据）
  - `_from_llm(eid)` → `gateway.chat()` 补充长尾词
- [ ] **A8-3** — `backend/app/service/keyword_service.py` — 实现 LLM 四层分类：
  - 输入关键词列表 → `gateway.chat()` → 归入 认知/选型/痛点/场景
  - 输出 `{ keyword, layer, source, lbs_tags }`
- [ ] **A8-4** — `backend/app/api/v1/user/keyword.py` — ⚠️ 新建路由文件：
  - `POST /user/keywords/generate` → 触发四源汇聚+LLM分类（异步 AgentTask）
  - `GET /user/keywords` → 分页列表（筛选 layer/source）
  - `POST /user/keywords` → 手动添加
  - `PUT /user/keywords/{id}` → 编辑
  - `DELETE /user/keywords/{id}` → 删除
- [ ] **A8-5** — `backend/tests/a_track/test_a8_keywords.py` — ⚠️ 新建，验证 CRUD/四层/来源/租户隔离/generate
- [ ] **A8-6** — `frontend/src/views/knowledge-base/Index.vue` — 新增词库四层面板（折叠/筛选/增删改/来源标签/LBS标签）
- [ ] **A8-7** — `frontend/src/api/kb.ts` — 加 keyword API 封装（generate/list/create/update/delete）
- [ ] **A8-8** — 验收：进度表 `A8 done`，发 **NOTIFY B（关键）**
- [ ] **A8-9** — `backend/tests/fixtures/handoff_a_to_b/keywords.json` — 按真实字段形状刷新

---

## W5–W8：前端 + 联调（A9）

---

### A9 · 前端：登录/入驻/KB/设置
> **现状态**：页面目录全有，API 封装全有，但接线程度不一（Login/Register 功能较完整，onboarding/settings 待完善）
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `frontend/src/views/Login.vue` | 登录页 | 🟡 待核实 |
| `frontend/src/views/Register.vue` | 注册页 | 🟡 待核实 |
| `frontend/src/views/onboarding/Index.vue` | 入驻引导页 | 🟡 骨架 |
| `frontend/src/views/knowledge-base/Index.vue` | KB 管理页 | 🟡 骨架 |
| `frontend/src/views/settings/Index.vue` | 设置页 | 🟡 骨架 |
| `frontend/src/api/auth.ts` | auth API 封装 | 🟢 已有 |
| `frontend/src/api/enterprise.ts` | enterprise API 封装 | 🟢 已有 |
| `frontend/src/api/kb.ts` | KB API 封装 | 🟢 已有 |
| `frontend/src/api/onboarding.ts` | onboarding API 封装 | 🟢 已有 |
| `frontend/src/stores/user.ts` | 用户状态（JWT 存储） | 🟢 已有 |
| `frontend/src/stores/onboarding.ts` | 入驻流程状态 | 🟢 已有 |
| `frontend/src/router/index.ts` | 路由配置 | 🟢 已有 |
| `frontend/src/utils/request.ts` | axios 封装 + JWT 注入 | 🟢 已有 |
| `frontend/src/layouts/DefaultLayout.vue` | 默认布局 | 🟢 已有 |
| `frontend/src/components/ProgressChain.vue` | 进度链组件 | 🟢 已有 |

- [ ] **A9-1** — `frontend/src/views/Login.vue` — 核实：邮箱+密码 → `api/auth.ts` login → 存 JWT 到 store → 跳转 `/onboarding` 或 `/strategy-pack`
- [ ] **A9-2** — `frontend/src/views/Register.vue` — 核实：企业名+邮箱+密码 → `api/auth.ts` register → 自动登录 → 跳转 `/onboarding`
- [ ] **A9-3** — `frontend/src/views/onboarding/Index.vue` — 完善 6 步表单：
  - Step 1 选行业(beauty_local) → Step 2 选主攻 AI(doubao/deepseek 多选) → Step 3 填品牌 → Step 4 填门店(含坐标) → Step 5 填服务 → Step 6 填客群+竞品+raw_inputs
  - 提交 → `api/onboarding.ts` run → SSE 进度条 → 100% 跳转 `/strategy-pack`
- [ ] **A9-4** — `frontend/src/views/knowledge-base/Index.vue` — 完善：
  - Fact / FAQ / Signal 三 tab，各含列表+新增/编辑弹窗
  - A8 词库四层面板（折叠/筛选/增删改）
- [ ] **A9-5** — `frontend/src/views/settings/Index.vue` — 完善：
  - 企业信息编辑 → `api/enterprise.ts` updateProfile
  - 主攻 AI 修改 → 改 `target_engines`（通过 settings JSON 或独立字段）
  - 成员管理 → list + invite + 改角色
- [ ] **A9-6** — `frontend/src/api/` — 核实/补全 API 封装：
  - `auth.ts` — register / login / getCurrentUser
  - `enterprise.ts` — getProfile / updateProfile / listMembers / inviteMember / updateMember
  - `kb.ts` — facts CRUD / faqs CRUD / signals CRUD + keywords CRUD（A8 新增）
  - `onboarding.ts` — run / status SSE
- [ ] **A9-7** — `frontend/src/router/index.ts` — 核实路由守卫：未登录→/login，已登录但无企业→/onboarding，已完成入驻→/strategy-pack
- [ ] **A9-8** — 手工烟雾测试：注册→登录→入驻→SSE→跳转 /strategy-pack 全链跑通
- [ ] **A9-9** — ⚠️ AC-13 联动：改 `target_engines` → B6 监测跟随之（需等 B6，**WAIT_FOR B6**）
- [ ] **A9-10** — 验收：进度表 `A9 done`

---

## GATE 联调

### G1 · 信封+JWT（W1–W2）
> A1 done + B 侧受保护 API 可鉴权

- [ ] **G1-1** — B 带 JWT 调 `GET /user/enterprise/profile` → `200`
- [ ] **G1-2** — B 无 JWT 调 → `401`
- [ ] **G1-3** — 进度表 `G1 done`

### G2 · 诊断→方案包（W4）
> A7+A8 done + B1 读真 API

- [ ] **G2-1** — B1 调 `GET /diagnosis/{id}` → source_map 非写死
- [ ] **G2-2** — B1 调 `GET /keywords` → 四层与 fixture 一致
- [ ] **G2-3** — B1 五区 mixed_weight = 0.6×model + 0.4×probe 正确
- [ ] **G2-4** — 进度表 `G2 done`

### G3 · 闸门→发布（W6）
> A0+A5 done + B4+B5

- [ ] **G3-1** — B4 禁词来自 IndustryPack（非硬编码）
- [ ] **G3-2** — B5 AUTO 托管页 URL 可访问
- [ ] **G3-3** — 进度表 `G3 done`

### G4 · T0/T1 Δ（W6）
> A7 T0 + B6 T1 → 可算 Δ

- [ ] **G4-1** — T0（baseline=true）与 T1 同 prompt 对齐
- [ ] **G4-2** — B7 dashboard `delta_mention` 可算
- [ ] **G4-3** — 进度表 `G4 done`

### G5 · AC-01 全链路（W8）
> A 过线 + B 过线

- [ ] **G5-1** — 8 步全链路跑通
- [ ] **G5-2** — A 侧 AC-04/05/14/15 + B 侧 AC 全 PASS
- [ ] **G5-3** — 进度表 `G5 done` → **MVP-A 验收**

---

## 新建文件清单（汇总）

| # | 文件路径 | 对应 Step |
|---|----------|:---------:|
| 1 | `backend/tests/a_track/test_a0_industry_pack.py` | A0-4 |
| 2 | `backend/tests/a_track/test_a1_auth.py` | A1-4 |
| 3 | `backend/tests/a_track/test_a2_kb.py` | A2-4 |
| 4 | `backend/tests/a_track/test_a3_gateway.py` | A3-4 |
| 5 | `backend/app/rag/faiss_service.py` | A4-1 |
| 6 | `backend/tests/a_track/test_a4_faiss.py` | A4-3 |
| 7 | `backend/tests/a_track/test_a5_onboarding.py` | A5-7 |
| 8 | `backend/tests/a_track/test_a6_sse.py` | A6-5 |
| 9 | `backend/tests/a_track/test_a7_diagnosis.py` | A7-9 |
| 10 | `backend/app/schemas/keyword.py` | A8-1 |
| 11 | `backend/app/service/keyword_service.py` | A8-2 |
| 12 | `backend/app/api/v1/user/keyword.py` | A8-4 |
| 13 | `backend/tests/a_track/test_a8_keywords.py` | A8-5 |

共 **13 个新文件**，其余 step 全部是修改已有文件。

---

## 每日检查清单

```
[ ] git pull → 读 G-L3-开发进度.md 最新状态
[ ] 今天做哪个 Step → 标记 doing
[ ] Step 完成后跑对应测试 → PASS → 标记 done
[ ] 若完成的是 Ax 整体 → 更新进度表 + commit + push
[ ] 若 Ax 有 NOTIFY → 群里发话术通知 B
[ ] 若产出影响 fixture → 同步刷新 handoff_a_to_b/
```

---

*开发者 A TODO v2.0 · 每 Step 精确到文件 · 对照手册 §11 测试验收*
