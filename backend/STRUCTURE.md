# GEO Backend 目录结构

详见 [docs/v4/GEO-项目目录结构.md](../docs/v4/GEO-项目目录结构.md)

## 快速对照 TalentFlow

| TalentFlow | GEO |
|------------|-----|
| `api/v1/auth.py`（共用） | `api/v1/auth.py` |
| `api/v1/skills.py` / `tasks.py`（横切） | `api/v1/llm.py` / `api/v1/agent.py` |
| `api/v1/user/`（按业务域） | `api/v1/user/`（三舱：enterprise/kb/content…） |
| `api/v1/admin/`（平台运维） | `api/v1/admin/`（enterprises/users/stats…） |
| `api/common.py` | `api/common.py`（require_role 装饰器） |
| `core/security.py` | `core/security.py`（密码+JWT+鉴权依赖） |
| `models/user.py` | `models/auth.py` |
| `schemas/user_schema.py` | `schemas/auth.py` + 按域拆分 |
| `mcp_server/` | `backend/mcp_server/` |

## API 注册方式（对齐 TalentFlow main.py）

每个 router **自带完整 prefix**（如 `/api/v1/auth`），在 `app/api/v1/__init__.py` 扁平 `include_router`，`main.py` 不再叠加 `/api/v1` 前缀。

```
app/api/v1/
├── auth.py          # 共用 · 认证
├── llm.py           # 共用 · LLM Gateway
├── agent.py         # 共用 · Agent 任务
├── user/            # 用户端 · 按业务域
│   ├── enterprise.py   → /api/v1/user/enterprise
│   ├── kb.py           → /api/v1/user/kb
│   ├── content.py      → /api/v1/user/content
│   └── ...
└── admin/           # 管理端 · 按业务域
    ├── enterprises.py  → /api/v1/admin/enterprises
    └── ...
```

## 常用 import

```python
from app.models import Enterprise, User, KBFact, Scenario
from app.schemas.strategy import StrategyPackResponse
from app.service import ContentService
```
