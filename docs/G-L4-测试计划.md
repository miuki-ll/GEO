# GEO 测试计划

> **版本**：v2.1 | **日期**：2026-07-16
> **关联**：[G-L3-实施清单.md](G-L3-实施清单.md) · [G-L1-需求规格说明书.md](G-L1-需求规格说明书.md)

---

## 1. 测试策略

| 层级 | 范围 | 工具 | 频率 |
|------|------|------|------|
| **单元测试** | service 层 / schemas 校验 / Agent 工具 | pytest + pytest-asyncio | 每次提交 |
| **集成测试** | API 端点 / Celery Job / EngineAdapter | pytest + httpx | 每次 PR |
| **E2E** | MVP-A 路径 8 步完整走通 | 种子数据 + 手动验证 | 每轮迭代 |
| **安全测试** | 租户隔离 / JWT / XSS / 跨租户 403 | 手动 + 自动化 | MVP 上线前 |

---

## 2. 单元测试

### 2.1 Service 层

```
tests/unit/service/
├── test_auth_service.py       # 注册/登录/JWT/密码哈希
├── test_kb_service.py         # Fact/FAQ/Signal CRUD + 租户隔离
├── test_diagnosis_service.py  # 探针结果解析·赛道判定·信源地图聚合
├── test_strategy_service.py   # 方案包构建·权重混合计算·闸门
├── test_content_service.py    # kb_fetch→LLM 链·RAG切片·分渠道格式化
├── test_publish_service.py    # AUTO→SEMI 降级·GUIDED 输出
├── test_monitor_service.py    # Core/Probe 池·T0/T1对比·临界检测
└── test_dashboard_service.py  # 效果舱聚合·四层漏斗
```

### 2.2 Schemas 校验

```
tests/unit/schemas/
├── test_auth_schemas.py       # 注册/登录字段校验
├── test_onboarding_schemas.py # 6步填表字段必填/类型/长度
├── test_strategy_schemas.py   # 方案包五区 schema extra=forbid
└── test_content_schemas.py    # content_unit schema 必填字段
```

### 2.3 Agent 工具

```
tests/unit/agents/
├── test_tool_registry.py      # 注册/调用/白名单拦截
├── test_industry_pack.py      # 行业包 9 方法返回值类型
└── test_harness.py            # ReAct step 单步调用
```

---

## 3. 集成测试

### 3.1 API 端点

```
tests/integration/api/
├── test_auth_api.py               # POST /register→login→/me
├── test_onboarding_api.py         # POST /run→GET /status SSE
├── test_diagnosis_api.py          # GET /diagnosis/{id}
├── test_kb_api.py                 # CRUD Fact/FAQ/Signal
├── test_strategy_pack_api.py      # GET draft→POST confirm
├── test_content_api.py            # GET drafts→bulk-approve
├── test_publish_api.py            # GET tasks→POST run
├── test_monitor_api.py            # GET results→compare
└── test_outcomes_api.py           # GET dashboard
```

### 3.2 Celery Job

```
tests/integration/jobs/
├── test_onboarding_graph.py       # onboarding_graph 4节点→100%
├── test_monitor_scheduled.py      # Celery Beat 定时监测
└── test_content_generation.py     # SkillRuntime 固定链
```

### 3.3 EngineAdapter

```
tests/integration/llm/
├── test_doubao_adapter.py         # 豆包 chat 调通
├── test_deepseek_adapter.py       # DeepSeek chat 调通
├── test_kimi_adapter.py           # Kimi chat 调通
├── test_wenxin_adapter.py         # 文心 chat 调通
└── test_gateway.py                # Gateway 路由重试
```

---

## 4. E2E 验收测试

### 4.1 种子数据

```bash
# 一键创建生美种子企业
python -m app.agents.industry.packs.beauty_local.seed
# 产出：1 enterprise + 1 owner + 20 Fact + 5 Signal + 5 Scenario
```

### 4.2 MVP-A 路径手动验收

```
□ 注册 / 登录
□ 开店向导 6 步填表（选主攻 AI doubao + 填 NAP + 项目 + 竞品 + RawInputs）
□ 点 [开始分析] → 进度条 0→100%
□ 诊断报告展示（信源地图·赛道判定·焦虑话术）
□ 四层词库确认/编辑（四源汇聚·来源标注）
□ 方案包五区展示（persona·竞品·scenario候选·渠道权重·词库折叠）
□ 勾选 2 个 scenario → 确认生成
□ 草稿列表（含 RAG 切片标记）
□ 人闸门策略+草稿合并页 → 确认
□ 托管页 AUTO 发布 → URL 可访问
□ 小红书 SEMI 导出包 → 含 title/body/tags/cover_hint/步骤
□ 24h 后监测结果 T1 vs T0 对比
□ 效果舱四层漏斗展示
□ 设置页修改主攻 AI → 监测 EngineAdapter 联动切换
```

---

## 5. 安全测试

```
tests/security/
├── test_tenant_isolation.py   # 用户A访问企业B的数据 → 403
├── test_jwt_expiry.py         # 过期 Token → 401
├── test_unauthorized.py       # 无 Token → 401
├── test_xss_hosted_page.py    # 托管页 HTML sanitize
├── test_rate_limit.py         # 限流 429
└── test_agent_tools_readonly.py  # Agent 写操作拒绝
```

---

## 6. 测试数据与 Mock

### 6.1 EngineAdapter Mock

```python
# tests/fixtures/llm_mock.py
MOCK_ENGINE_RESPONSE = {
    "doubao": {"content": "根据搜索结果，静安区推荐以下皮肤管理中心...",
               "citations": ["dianping.com/shop/xxx", "zhihu.com/question/yyy"]},
    "deepseek": {...}
}
```

### 6.2 Faiss Mock

```python
# 测试环境降级为 in-memory
# Faiss 索引文件: tests/fixtures/faiss/
```

---

## 7. CI 流水线

```yaml
# .github/workflows/test.yml
name: GEO Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_DB: geo_test, POSTGRES_USER: geo, POSTGRES_PASSWORD: test }
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: pytest tests/unit/ --cov=backend/app
      - run: pytest tests/integration/ --cov-append
      - run: pytest tests/security/ --cov-append
```

---

## 8. 验收门禁

| 门禁 | 标准 | 阻塞上线 |
|------|------|:--:|
| 单元测试覆盖率 | ≥ 60% | ✅ |
| API 集成测试 | 10 模块全通过 | ✅ |
| MVP-A 路径 | 8 步手动跑通 | ✅ |
| 租户隔离 | 跨 enterprise 403 | ✅ |
| LLM Gateway | 4 Adapter 通 | ✅ |
| AC-01~AC-15 | 全部通过 | ✅ |

---

*测试计划 v2.1 · 对齐 AC-01~AC-15*
