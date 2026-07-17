# SPEC：AutoInitManager（FastAPI 全局资源生命周期管理器）

> **文档类型**：AI Coding 可复现技术规格  
> **权威实现**：`talentflow-ai-backend-bak/app/infrastructure/bootstrap/`  
> **迁移说明（概念层）**：[step-0-6-init-manager.md](../steps/step-0-6-init-manager.md)  
> **Gate**：`scripts/gate/steps/step_0_6.yaml` + `tests/unit/test_init_manager.py`  
> **更新日期**：2026-07-16

本文档供 AI coding 工具 / 工程师 **从零复现或移植** AutoInitManager。  
不要只照抄业务钩子内容；**必须先实现 Manager 契约**，再按「注册表」挂资源。

---

## 0. 一句话目标

按进程角色（`api` / `worker` / `mcp`）统一管控资源的 **init / stop**：

- 避免 Embedding / Reranker / LangGraph **重复加载**
- 避免 checkpoint / 连接 **泄漏**
- 保证 API 与 Celery Worker **启动行为可预期且一致**
- 把初始化状态暴露给 `/health/ready`

---

## 1. 问题与约束

### 1.1 改造前问题

| 问题 | 表现 |
|------|------|
| 初始化散落 | `main.py` lifespan、Celery 入口、模块全局各写一套 |
| 模型重复加载 | API 误加载 Reranker，内存暴涨 |
| 连接泄漏 | 有 init 无对称 stop |
| 不可观测 | 健康检查无法知道「哪些资源 init 失败」 |

### 1.2 硬约束（复现时不得省略）

1. **幂等**：`start()` / `stop()` 多次调用安全。
2. **角色过滤**：仅执行 `roles` 包含当前 `APP_PROCESS_ROLE` 的钩子。
3. **优先级**：`priority` 数字越小越先执行；`stop` 对过滤后的列表 **逆序**。
4. **critical**：关键失败必须 raise 阻断启动；非关键失败只记 status 并继续。
5. **资源容器**：`app.state.resources: dict`；无 FastAPI 时用 stub。
6. **同步/异步钩子都支持**：`inspect` 检测，可 await。
7. **后台任务**：`schedule_background`；`stop` 时 cancel 并等待。
8. **测试可重置**：`reset_for_tests()`。

---

## 2. 目录与文件清单（必须创建）

在 backend 包根（本项目为 `talentflow-ai-backend-bak/`）下：

```
app/infrastructure/bootstrap/
  __init__.py
  init_manager.py          # AutoInitManager + 单例 auto_init
  deps.py                  # get_resources / 可选 graph 兼容
  registrations/
    __init__.py
    register_all.py        # 集中注册；import 时副作用调用 register_all()
    database.py            # 示例：critical DB init
    langsmith.py           # 示例：api+worker
    langgraph.py           # 示例：worker init + stop
    embeddings.py          # 示例：可选预热 + schedule_background
    reranker.py            # 示例：worker only
```

挂接点：

| 进程 | 文件 | 行为 |
|------|------|------|
| API | `app/main.py` | `import register_all`；lifespan 内 `await auto_init.start(app)` / `stop()` |
| Worker | `app/core/celery_app.py` | `worker_process_init` → `asyncio.run(auto_init.start(stub))`；shutdown → `stop()` |
| Health | `app/api/health.py` | `_check_auto_init()` 读 `auto_init.get_status()` |
| Config | `app/core/config.py` | `APP_PROCESS_ROLE`、`PRELOAD_MODELS_ON_STARTUP` |
| Compose | `docker-compose.yml` | `APP_PROCESS_ROLE: api` / `worker` |

---

## 3. 配置项

```python
# app/core/config.py（Settings 字段）
APP_PROCESS_ROLE: str = os.getenv("APP_PROCESS_ROLE", "api")
# 取值：api | worker | mcp（大小写不敏感，strip 后 lower）

PRELOAD_MODELS_ON_STARTUP: bool = (
    os.getenv("PRELOAD_MODELS_ON_STARTUP", "false").lower() in ("1", "true", "yes")
)
```

Docker Compose 示例：

```yaml
backend:
  environment:
    APP_PROCESS_ROLE: api
    PRELOAD_MODELS_ON_STARTUP: ${PRELOAD_MODELS_ON_STARTUP:-false}

celery-worker:
  environment:
    APP_PROCESS_ROLE: worker
```

---

## 4. 核心 API 契约（必须逐条实现）

### 4.1 `_LifecycleItem`

```python
@dataclass(order=True)
class _LifecycleItem:
    priority: int
    name: str = field(compare=False)
    func: InitFunc = field(compare=False)
    roles: tuple[str, ...] = field(compare=False, default=("api", "worker", "mcp"))
    critical: bool = field(compare=False, default=True)
```

- `order=True` + 仅 `priority` 参与比较 → `sorted(items)` 按优先级。

### 4.2 `AutoInitManager` 公共方法

| 方法 | 语义 |
|------|------|
| `register_init(func, *, name=None, priority=100, roles=(...), critical=True)` | 追加 init 钩子 |
| `register_stop(func, *, name=None, priority=100, roles=(...), critical=False)` | 追加 stop 钩子；默认非 critical |
| `start(app=None)` | 幂等；过滤 roles；升序执行；写 `_status`；critical 失败 raise |
| `stop()` | 幂等；cancel 后台任务；过滤后 **逆序** stop |
| `schedule_background(coro)` | `asyncio.create_task` 并纳入 `_background_tasks` |
| `get_status()` | `{started, stopped, role, items}` |
| `reset_for_tests()` | 清空注册与状态（仅测试） |

### 4.3 `_call` 规则

```text
若函数签名含参数名 "app"：
  result = func(app)
否则：
  result = func()
若 result 为 awaitable：
  return await result
否则：
  return result
```

### 4.4 `start` 状态写入

成功：

```python
self._status[item.name] = {
    "status": "ok",
    "duration_ms": <int>,
    "role": <current_role>,
}
```

失败：

```python
self._status[item.name] = {
    "status": "failed",
    "duration_ms": <int>,
    "error": str(exc),
    "role": <current_role>,
}
```

- critical=True → `raise`
- critical=False → `logger.warning` 后继续下一个

### 4.5 `start` 前必须

```python
if app is not None:
    if not hasattr(app.state, "resources") or app.state.resources is None:
        app.state.resources = {}
```

### 4.6 模块单例

```python
auto_init = AutoInitManager()
```

全项目共用这一份（测试可用独立实例或 `reset_for_tests`）。

**权威源码参考**：`app/infrastructure/bootstrap/init_manager.py`（完整实现约 200 行，可直接对齐）。

---

## 5. 注册表（本项目现行矩阵）

`register_all.py` 必须在 **import 时调用** `register_all()`（副作用注册），以便 `main.py` / Celery 只需：

```python
import app.infrastructure.bootstrap.registrations.register_all  # noqa: F401
```

### 5.1 注册矩阵

| name | type | priority | roles | critical | 职责摘要 |
|------|------|----------|-------|----------|----------|
| langsmith | init | 5 | api, worker | True(默认) | 打开 LangSmith tracing；写 `resources["langsmith"]` |
| database | init | 10 | api, worker, mcp（默认） | **True** | load ORM、create 补充表；写 `resources["database"]` |
| langgraph | init | 40 | **worker** | False | `init_smart_apply_graph`；写 `resources["langgraph"]` |
| embeddings | init | 50 | api, worker | False | 若 PRELOAD=false 跳过；否则 `schedule_background` 预热 |
| reranker | init | 55 | **worker** | False | `get_reranker()`；写 `resources["reranker"]` |
| langgraph_stop | stop | 40 | api, worker | False | `shutdown_smart_apply_graph`；pop resources |

### 5.2 角色加载结果（验收用）

| 资源 | api | worker |
|------|-----|--------|
| database | ✅ | ✅ |
| langsmith | ✅ | ✅ |
| embeddings | ✅（可跳过预热） | ✅ |
| langgraph（register_init） | ❌ | ✅ |
| reranker | ❌ | ✅ |
| langgraph_stop | ✅（若曾加载） | ✅ |

> API 在 `PRELOAD_MODELS_ON_STARTUP=true` 时，可通过 embeddings 后台任务 **额外** 调用 `init_langgraph(app)`，这是预热优化，不改变「register_init roles=worker」的矩阵语义。

### 5.3 各 registration 钩子契约

**database.py**

```text
def init_database(app: FastAPI) -> None:
  - 创建 uploads 目录（按项目需要）
  - load_all_models()
  - 可选 SQLModel.metadata.create_all 补充表
  - app.state.resources["database"] = {"status": "ok"}
```

**langgraph.py**

```text
async def init_langgraph(app: FastAPI) -> None:
  - await init_smart_apply_graph()
  - app.state.resources["langgraph"] = <graph 句柄>

async def stop_langgraph(app: FastAPI) -> None:
  - await shutdown_smart_apply_graph()
  - app.state.resources.pop("langgraph", None)
```

**embeddings.py**

```text
def init_embeddings(app: FastAPI) -> None:
  - if not PRELOAD_MODELS_ON_STARTUP:
      resources["embeddings"] = {"preloaded": False}; return
  - role==api: schedule_background(warmup embeddings + init_langgraph)
  - else: schedule_background(warmup embeddings only)
  - resources["embeddings"] = {"preloaded": "background"}
```

**reranker.py**

```text
def init_reranker(app: FastAPI) -> None:
  - reranker = get_reranker()  # 内部应再按 role 决定是否真加载
  - resources["reranker"] = {"loaded": reranker is not None}
```

**langsmith.py**

```text
def init_langsmith(app: FastAPI) -> None:
  - enabled = setup_langsmith_tracing()
  - resources["langsmith"] = {"enabled": enabled}
```

---

## 6. 进程挂接（必须实现）

### 6.1 FastAPI lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.infrastructure.bootstrap.init_manager import auto_init
import app.infrastructure.bootstrap.registrations.register_all  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    await auto_init.start(app)
    yield
    await auto_init.stop()

app = FastAPI(lifespan=lifespan)
```

### 6.2 Celery Worker（无 FastAPI 实例）

```python
from types import SimpleNamespace
from celery.signals import worker_process_init, worker_process_shutdown
import asyncio, os

def _worker_app_stub():
    return SimpleNamespace(state=SimpleNamespace(resources={}))

@worker_process_init.connect
def _on_worker_process_init(**_kwargs):
    os.environ.setdefault("APP_PROCESS_ROLE", "worker")
    from app.infrastructure.bootstrap.init_manager import auto_init
    import app.infrastructure.bootstrap.registrations.register_all  # noqa: F401
    asyncio.run(auto_init.start(_worker_app_stub()))

@worker_process_shutdown.connect
def _on_worker_process_shutdown(**_kwargs):
    from app.infrastructure.bootstrap.init_manager import auto_init
    asyncio.run(auto_init.stop())
```

**要点**：stub 必须提供 `state.resources`，以便 `init_*(app)` 签名不变。

### 6.3 Depends 读取资源

```python
# app/infrastructure/bootstrap/deps.py
def get_resources(request: Request) -> dict:
    return getattr(request.app.state, "resources", {}) or {}
```

### 6.4 Health 聚合

```python
def _check_auto_init() -> str:
    status = auto_init.get_status()
    if not status.get("started"):
        return "pending"
    for info in status.get("items", {}).values():
        if info.get("status") == "failed":
            return "fail"
    return "ok"
```

将 `"auto_init"` 纳入 `/health/ready` 的必需检查项。

---

## 7. 单元测试验收清单（必须全绿）

文件：`tests/unit/test_init_manager.py`

| 用例 | 断言 |
|------|------|
| sync + async init | 按 priority 顺序执行 |
| start 幂等 | 第二次 start 不重复执行钩子 |
| stop 幂等 | 第二次 stop 不重复 |
| roles 过滤 | `APP_PROCESS_ROLE=api` 时不跑 `roles=("worker",)` |
| critical 失败 | `start` raise |
| 非 critical 失败 | 继续后续钩子；`get_status()["items"][name]["status"]=="failed"` |
| app.state.resources | init 写入后可读 |

运行：

```bash
cd talentflow-ai-backend-bak
python -m pytest tests/unit/test_init_manager.py -q
python scripts/gate/run_gate.py --step 0.6
```

---

## 8. 给 AI Coding 的实现步骤（按序执行）

1. 创建 `init_manager.py`，实现第 4 节全部契约 + 单例 `auto_init`。
2. 写 `test_init_manager.py`，**先让 Manager 单测全绿**（不依赖 DB/模型）。
3. 增加 Settings：`APP_PROCESS_ROLE`、`PRELOAD_MODELS_ON_STARTUP`。
4. 实现 `registrations/*` 与 `register_all()`（可先 stub 钩子，再换真实业务）。
5. 改造 `main.py` lifespan 接入 start/stop。
6. 改造 Celery signals + stub。
7. Compose 设置 `APP_PROCESS_ROLE`。
8. Health 接入 `get_status()`。
9. 跑 Gate 0.6；修到 PASS。

**禁止**：在 API/Worker 再次手写平行的「全局 init 列表」绕过 Manager。

---

## 9. 扩展新资源的标准姿势

```python
# registrations/foo.py
def init_foo(app: FastAPI) -> None:
    app.state.resources["foo"] = {"status": "ok"}

def stop_foo(app: FastAPI) -> None:
    app.state.resources.pop("foo", None)

# register_all.py
auto_init.register_init(init_foo, name="foo", priority=60, roles=("api", "worker"), critical=False)
auto_init.register_stop(stop_foo, name="foo_stop", priority=60, roles=("api", "worker"))
```

原则：

- 大模型 / 重资源 → 尽量限制 `roles`（如仅 worker）
- 基础设施（DB）→ critical=True，priority 靠前
- 可降级能力 → critical=False

---

## 10. 已知边界（复现时勿过度承诺）

| 项 | 现状 |
|----|------|
| MCP 进程 | `roles` 预留 `"mcp"`；本仓库 MCP 入口 **尚未** 统一调 `auto_init.start()`，仍有独立 `load_all_models()` |
| register_all 副作用 | import 即注册；测试注意单例污染，用 `reset_for_tests` 或新 Manager 实例 |
| stop 逆序 | 仅对 **过滤后** 的 stop 列表 reverse，不是全局所有 hook |

---

## 11. 参考源码路径（本仓库）

| 路径 | 用途 |
|------|------|
| `app/infrastructure/bootstrap/init_manager.py` | Manager 权威实现 |
| `app/infrastructure/bootstrap/registrations/register_all.py` | 注册矩阵 |
| `app/main.py` | API lifespan |
| `app/core/celery_app.py` | Worker 信号 |
| `app/api/health.py` | ready 探针 |
| `tests/unit/test_init_manager.py` | 行为验收 |
| `scripts/gate/steps/step_0_6.yaml` | Gate 门禁 |

---

## 12. 完成定义（Definition of Done）

- [ ] Manager 单测 7 类行为全绿
- [ ] API lifespan + Worker signals 均调用同一 `auto_init`
- [ ] `APP_PROCESS_ROLE` 控制 reranker/langgraph 不在 api 误加载（register 矩阵生效）
- [ ] `/health/ready` 含 `auto_init`
- [ ] `run_gate.py --step 0.6` PASS（离线至少 T0.6.1–T0.6.8、T0.6.11）
