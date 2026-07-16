# GEO 部署运维手册

> **版本**：v2.1 | **日期**：2026-07-16
> **关联**：[G-L2-架构设计说明书.md](G-L2-架构设计说明书.md)

---

## 1. 部署架构

```
Docker Compose 6 容器：

  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │   web    │  │   api    │  │ celery   │
  │ :80→5173 │  │  :8000   │  │  worker  │
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │    pg    │  │  redis   │  │  celery  │
  │   :5432  │  │  :6379   │  │   beat   │
  └──────────┘  └──────────┘  └──────────┘
```

---

## 2. 首次部署

### 2.1 环境要求

```
- Docker 24+
- Docker Compose v2
- 4C8G 服务器（最低）
- 域名 + SSL（生产）
```

### 2.2 启动步骤

```bash
# 1. 克隆代码
git clone <repo-url> geo-platform
cd geo-platform

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env：填写 API Key、DB密码、SECRET_KEY

# 3. 构建 & 启动
docker compose build
docker compose up -d

# 4. 数据库迁移
docker compose exec api alembic upgrade head

# 5. 种子数据（可选）
docker compose exec api python -m app.agents.industry.packs.beauty_local.seed

# 6. 验证
curl http://localhost:8000/api/v1/health   # → {"status": "ok"}
curl http://localhost:5173                  # → 前端页面
```

### 2.3 环境变量清单

```bash
# backend/.env

# === App ===
APP_ENV=production
SECRET_KEY=<随机生成64位>
API_V1_PREFIX=/api/v1

# === Database ===
DATABASE_URL=postgresql://geo:<password>@pg:5432/geo

# === Redis / Celery ===
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# === LLM Engines ===
DOUBAO_API_KEY=xxx
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DEEPSEEK_API_KEY=xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
KIMI_API_KEY=xxx
KIMI_BASE_URL=https://api.moonshot.cn/v1
WENXIN_API_KEY=xxx
WENXIN_SECRET_KEY=xxx

# === Observability ===
SENTRY_DSN=xxx
LANGSMITH_API_KEY=xxx
LANGSMITH_PROJECT=geo-local-mvp

# === OSS ===
OSS_ENDPOINT=xxx
OSS_ACCESS_KEY=xxx
OSS_SECRET_KEY=xxx
OSS_BUCKET=geo-hosted-pages

# === JWT ===
JWT_SECRET_KEY=<随机生成>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

---

## 3. 日常运维

### 3.1 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs api -f --tail=100
docker compose logs celery_worker -f

# 重启服务
docker compose restart api
docker compose restart celery_worker

# 数据库备份
docker compose exec pg pg_dump -U geo geo > backup_$(date +%Y%m%d).sql

# 数据库恢复
docker compose exec -T pg psql -U geo geo < backup_20260716.sql

# Alembic 迁移
docker compose exec api alembic revision --autogenerate -m "描述"
docker compose exec api alembic upgrade head

# 进入 shell
docker compose exec api python           # Python REPL
docker compose exec pg psql -U geo geo   # PostgreSQL CLI
```

### 3.2 监控检查

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# Celery worker 状态
docker compose exec celery_worker celery -A app.core.celery_app inspect active

# Redis 连接
docker compose exec redis redis-cli ping   # → PONG

# 数据库连接
docker compose exec pg pg_isready -U geo

# Faiss 索引
docker compose exec api python -c "from app.core.embedding import check_faiss; check_faiss()"
```

---

## 4. 故障处理

### 4.1 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| API 502/503 | api 容器挂了 | `docker compose restart api` |
| Celery 任务堆积 | worker 挂了 | `docker compose restart celery_worker` |
| 数据库连接超时 | pg 容器挂了 | `docker compose restart pg` |
| LLM 调用超时 | API Key 过期或限流 | 检查 `.env` API Key · 看 Sentry 错误 |
| Faiss 索引丢失 | 容器重建导致文件丢失 | `docker compose exec api python -m app.tasks.rebuild_faiss` |
| Redis 内存满 | 任务结果堆积 | `docker compose exec redis redis-cli FLUSHDB` |

### 4.2 回滚

```bash
# 代码回滚
git log --oneline -5
git revert <commit-hash>
docker compose build api && docker compose up -d api

# 数据库回滚
docker compose exec api alembic downgrade -1

# 全量回滚到上一个稳定版本
docker compose down
git checkout <stable-tag>
docker compose build --no-cache
docker compose up -d
docker compose exec api alembic upgrade head
```

---

## 5. 生产扩展路径

### 5.1 V1.1 上云（ECS + RDS）

```
当前 MVP（Docker Compose 单机）
  → V1.1 拆分：

  前端      → S3 + CloudFront (CDN)
  API       → ECS Fargate (auto-scale 2-4 instances)
  Celery    → ECS Fargate (独立 service)
  数据库    → RDS PostgreSQL (Multi-AZ · 自动备份)
  缓存      → ElastiCache Redis (Cluster mode)
  存储      → S3 (托管页静态文件 · Faiss 索引备份)
  域名/SSL  → ALB + ACM
```

### 5.2 备份策略

| 数据 | 频率 | 保留 |
|------|------|------|
| PostgreSQL | 每日 (RDS auto) | 7 天 |
| Faiss 索引 | 每日 (S3 sync) | 30 天 |
| 托管页 HTML | 实时 (S3) | 永久 |

---

## 6. Celery 调度

### 6.1 Worker 启动

```bash
# 开发
celery -A app.core.celery_app worker -l info -P solo

# 生产
celery -A app.core.celery_app worker -l info -c 4
```

### 6.2 Beat 调度

```bash
celery -A app.core.celery_app beat -l info

# 定时任务配置 (celery_app.py)：
# - monitor_core_weekly: 每周一 9:00 跑 Core 监测
# - monitor_probe_weekly: 每周三 9:00 跑 Probe 监测
# - outcome_snapshot_daily: 每日 6:00 生成效果快照
# - kb_freshness_check: 每日 8:00 检查 KB 新鲜度
```

---

*部署运维手册 v2.1*
