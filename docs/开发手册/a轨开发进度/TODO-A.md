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

- [x] **[A5-1](./steps/A5-1.md)** — 🛠️ 重写 `nodes.py`：4 个 LLM 节点（DIAGNOSE→PAIN→PERSONA→COMPETITOR）+ 并行 search 兜底
- [x] **[A5-2](./steps/A5-2.md)** — 🛠️ `onboarding.py` 改造：新 `OnboardingRunRequest` schema + 切 `runner.run_graph()` + Brand/Store/Service 副作用写入
- [x] **[A5-3](./steps/A5-3.md)** — 🛠️ KB 自动建库：seed_facts → KBFact/KBSignal + thin_kb_check + llms.txt 骨架
- [x] **[A5-4](./steps/A5-4.md)** — 🧪 新建 `test_a5_onboarding.py`，6 条用例（mock LLM 全流程）
- [x] **🔍 A5 验收（审查者）** — ✅ 审查通过（2026-07-19）：代码质量好，4 节点 LLM + 并行 search 兜底 + 副作用写入 + KB 自动建库设计合理。已 NOTIFY B → G3

### A6 · onboarding SSE 进度
> **方案**：Redis pub/sub SSE 实时推送 — `core/sse.py` 封装 + nodes/runner 发布事件 + `/events/{task_id}` 端点
> **现状态**：`GET /status/{task_id}` 已是轮询接口，待升级为 SSE
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/core/sse.py` | Redis pub/sub 封装（publish / subscribe generator） | 🔴 待建 |
| `backend/app/api/v1/user/onboarding.py` | 新增 `GET /events/{task_id}` SSE 端点 | 🛠️ 待改 |
| `backend/app/agents/graphs/onboarding/nodes.py` | 每个节点完成后 publish 进度事件 | 🛠️ 待改 |
| `backend/app/agents/runner.py` | graph 开始/失败时 publish 事件 | 🛠️ 待改 |

- [x] **[A6-1](./steps/A6-1.md)** — 🆕 `core/sse.py` + 🛠️ nodes/runner/onboarding 接 Redis pub/sub SSE
- [x] **[A6-2](./steps/A6-2.md)** — 🧪 新建 `test_a6_sse.py`，4 条用例（mock Redis）
- [x] **🔍 A6 验收（审查者）** — ✅ 审查通过（2026-07-19）：Redis pub/sub SSE 设计干净，4 条测试覆盖完整，向后兼容轮询接口

---

## W3：诊断（A7）

---

### A7 · 诊断 5 项 + 写 T0 ⚠️ 部分已有，需补全
> **方案**：Celery 异步 + 并行 search（≤5）+ `search_results` 独立表 + 非豆包跳过
> **现状态**：`diagnosis.py` 路由存在，`diagnosis_service.py` 硬编码假数据
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/models/strategy.py` | 新增 `SearchResult` 模型 | 🛠️ 待改 |
| `backend/app/models/auth.py` | Enterprise 加 `search_results` relationship | 🛠️ 待改 |
| `backend/app/models/__init__.py` | 导出 SearchResult | 🛠️ 待改 |
| `backend/app/schemas/diagnosis.py` | 新增 SearchCitation/SearchResult*/SourceMap/DiagnosisFullResponse | 🛠️ 待改 |
| `backend/app/service/diagnosis_service.py` | 重写：generate_probes/batch_search/analyze_from_citations/build_source_map/write_t0_baseline | 🛠️ 重写 |
| `backend/app/api/v1/user/diagnosis.py` | POST /all 改 Celery + GET /{batch_no} 五区 JSON + SSE events | 🛠️ 待改 |
| `backend/app/tasks/all_tasks.py` | diagnosis_run 改调新 service + SSE publish | 🛠️ 待改 |
| `backend/app/models/monitor.py` | MonitorResult（T0 写入目标，baseline 字段已有） | 🟢 已有 |
| `backend/app/core/llm/gateway.py` | A3 gateway.chat() + gateway.search() | 🟢 已有 |

- [x] **[A7-1](./steps/A7-1.md)** — 🆕 `search_results` 独立表 + schema（SearchCitation/SearchResult*/SourceMap/DiagnosisFullResponse）+ migration
- [x] **[A7-2](./steps/A7-2.md)** — 🛠️ 重写 `diagnosis_service.py`：generate_probes → batch_search(Celery+并发5) → analyze → source_map → write_t0
- [x] **[A7-3](./steps/A7-3.md)** — 🛠️ `diagnosis.py` 路由改造：POST /all 调 Celery + GET /{batch_no} 五区 JSON + SSE events
- [x] **[A7-4](./steps/A7-4.md)** — 🧪 新建 `test_a7_diagnosis.py`，5 条用例（mock LLM + search）
- [ ] **🔍 A7 验收（审查者）** — 读执行记录 + git diff + 跑测试 → 更新进度表 + NOTIFY B（关键）

### ✅ A7 已确定

| # | 问题 | 决策 |
|---|------|------|
| 1 | 并发方案 | **Celery + asyncio.Semaphore(5)** 并行 search |
| 2 | 非豆包引擎 | **跳过**（不调 chat 模拟） |
| 3 | citations 持久化 | **`search_results` 独立表**（JSON 存 citations） |

---

## W4：词库（A8）

---

### A8 · 四源汇聚词库 + CRUD + generate ⚠️ 整模块缺失
> **方案**：Keyword 保留现有字段 + 新增 layer/source/lbs_tags + Enterprise 加 raw_inputs 持久化 + Celery 异步 generate + 按 phrase 去重
> **现状态**：`keywords` 表在 `models/strategy.py`，但无独立路由/service/schema
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `backend/app/models/strategy.py` | Keyword 加 layer/source/lbs_tags | 🛠️ 待改 |
| `backend/app/models/auth.py` | Enterprise 加 raw_inputs | 🛠️ 待改 |
| `backend/app/schemas/keyword.py` | KeywordCreate/Update/Response/ListParams/GenerateResponse/LayerSummary | 🔴 待建 |
| `backend/app/service/keyword_service.py` | 四源汇聚 + LLM 四层分类 + CRUD | 🔴 待建 |
| `backend/app/api/v1/user/keyword.py` | generate（Celery）+ CRUD + SSE events + 四层汇总 | 🔴 待建 |
| `backend/app/tasks/all_tasks.py` | 新增 keyword_generate Celery 任务 | 🛠️ 待改 |
| `backend/app/core/llm/gateway.py` | A3 gateway.chat() | 🟢 已有 |
| `backend/app/service/diagnosis_service.py` | A7 search_results（探针来源） | 🟡 依赖 A7 |
| `backend/app/api/v1/user/onboarding.py` | A5 raw_inputs 写入 Enterprise | 🟡 依赖 A5 |

- [x] **[A8-1](./steps/A8-1.md)** — 🛠️ Keyword 加 layer/source/lbs_tags + Enterprise 加 raw_inputs + schema 新建 + migration
- [x] **[A8-2](./steps/A8-2.md)** — 🆕 `keyword_service.py`：四源汇聚 + LLM 四层分类 + CRUD
- [x] **[A8-3](./steps/A8-3.md)** — 🆕 `keyword.py` 路由：POST /generate（Celery）+ CRUD + SSE events + 四层汇总
- [x] **[A8-4](./steps/A8-4.md)** — 🧪 新建 `test_a8_keywords.py`，6 条用例（mock LLM）
- [ ] **🔍 A8 验收（审查者）** — 读执行记录 + git diff + 跑测试 → 更新进度表 + NOTIFY B（关键）

### ✅ A8 已确定

| # | 问题 | 决策 |
|---|------|------|
| 1 | Keyword 模型字段 | **保留现有 + 新增** layer/source/lbs_tags |
| 2 | raw_inputs 持久化 | **Enterprise.raw_inputs**（A5 入驻时写入） |
| 3 | generate 方式 | **Celery 异步** + SSE 进度 |
| 4 | 去重策略 | 同 enterprise 内 **phrase 相同跳过** |

---

## W5–W8：前端 + 联调（A9）

---

### A9 · 前端：登录/入驻/KB/设置
> **方案**：只接后端 API（不改 UI 布局）+ 分步收集表单数据 + SSE 进度 + 路由守卫按入驻状态跳转
> **现状态**：页面目录全有，API 封装全有，但接线程度不一（Login/Register 功能较完整，onboarding/settings 待完善）
> **涉及文件**：

| 文件 | 作用 | 状态 |
|------|------|:--:|
| `frontend/src/views/onboarding/Index.vue` | 入驻引导页 — 补齐表单字段 + SSE 进度 | 🛠️ 待改 |
| `frontend/src/views/knowledge-base/Index.vue` | KB 管理页 — 接真实 CRUD + 词库面板 | 🛠️ 待改 |
| `frontend/src/views/settings/Index.vue` | 设置页 — 企业信息 + 团队成员接真实 API | 🛠️ 待改 |
| `frontend/src/api/onboarding.ts` | 更新 OnboardingRunRequest 类型 + SSE 函数 | 🛠️ 待改 |
| `frontend/src/api/kb.ts` | 新增 keyword API 函数 | 🛠️ 待改 |
| `frontend/src/stores/onboarding.ts` | 扩展 persist 字段 | 🛠️ 待改 |
| `frontend/src/router/index.ts` | 路由守卫加入驻状态判断 | 🛠️ 待改 |
| `frontend/src/views/Login.vue` | 登录页 | 🟢 已可用 |
| `frontend/src/views/Register.vue` | 注册页 | 🟢 已可用 |

- [x] **[A9-1](./steps/A9-1.md)** — 🛠️ 入驻向导：更新 API 类型 + 补齐表单字段 + SSE 进度 + 分步收集数据
- [x] **[A9-2](./steps/A9-2.md)** — 🛠️ 知识库：Fact/FAQ 接真实 CRUD + 新增词库四层面板
- [x] **[A9-3](./steps/A9-3.md)** — 🛠️ 设置页：企业信息 + 团队成员接真实 API + 路由守卫按入驻状态跳转
- [x] **[A9-4](./steps/A9-4.md)** — 🔍 前端全链路验证：vue-tsc 类型检查 + 手工烟雾测试（10 步）
  > 注：vue-tsc ✅；API 烟雾 S1–S4/S6–S10 ✅；S5 SSE/LLM 受环境限制见执行记录（副作用仍写入）
- [ ] **🔍 A9 验收（审查者）** — 读执行记录 + git diff + 手工验证关键路径

### ✅ A9 已确定

| # | 问题 | 决策 |
|---|------|------|
| 1 | 入驻表单策略 | **分步收集**，最后一次性 POST /run |
| 2 | 入驻进度 | **切换 SSE**（A6 GET /events/{task_id}） |
| 3 | 登录后跳转 | **按入驻状态**：未入驻 → /onboarding，已入驻 → /outcomes |
| 4 | A9 范围 | **只接后端 API**，不改 UI 布局 |

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
