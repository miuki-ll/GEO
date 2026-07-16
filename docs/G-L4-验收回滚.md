# ROLLBACK 验收 & 回滚基线

> **版本**：v1.0 · MVP-A | **日期**：2026-07-14  
> **关联**：`PRD.md` · `G-L2-架构设计说明书.md` · `G-L2-设计规范.md`

---

## 一、基础信息

| 项目 | 值 |
|------|-----|
| 产品版本 | MVP-A（首发最小路径） |
| 迭代编号 | `feat-mvp-beauty-local` |
| 行业 | `beauty_local` 生美（生活美容/皮肤管理） |
| 基线 Git Commit | `13fdcb4`（refactor: migrate backend from geo_core to app/ layout） |
| 部署方式 | Docker Compose（3 容器：api + web + pg） |

---

## 二、迭代交付验收标准

### 2.1 业务功能验收（对标 PRD.md）

**MVP-A 最小路径（AC-01）：**

| 步 | 动作 | 预期 |
|----|------|------|
| 1 | 开店向导提交 | job 链启动，SSE 进度条推进 |
| 2 | 方案包确认（勾选 2 个 scenario） | strategy_pack confirmed，闸门①写入 approval_log |
| 3 | 草稿生成（FAQ + 1 篇小红书） | fact_refs 非空，fact_verify 通过 |
| 4 | 人工审核通过 | draft → ready，闸门② |
| 5 | 托管页 AUTO 发布 | publish_task.content_asset_id 非空 |
| 6 | 小红书 SEMI 导出 | 含 title/body/tags/cover_hint/步骤说明 |
| 7 | Core 监测 1 轮 | monitor_results 入库 |
| 8 | 效果舱 Dashboard | AI KPI + 流量 + 发布追踪正常渲染 |

**核心验收项：**

- [ ] **AC-02** fact_refs 可追溯：参数/价格可定位到 `kb_facts.id`
- [ ] **AC-03** 禁词拦截：生美 9 类禁词 + 广告法禁词拒发；含 AI 生成标识
- [ ] **AC-04** 主攻 engine Core：≥1 engine 完成周监测
- [ ] **AC-05** 租户隔离：跨 enterprise → HTTP 403
- [ ] **AC-06** 2 次闸门：方案包 confirm + 草稿 approve，approval_log 有记录
- [ ] **AC-07** SEMI 标准包：所有必要字段完整
- [ ] **AC-08** 方案包五区：A/B/C/D/E 完整渲染
- [ ] **AC-09** scenario ≤ 5：勾选上限生效
- [ ] **AC-10** 三舱导航：舱1→2→3 可自由切换
- [ ] **AC-11** Faiss 聚类：pain_mine 去重+聚类可用
- [ ] **AC-12** Agent trace：agent_traces 落库可查
- [ ] **AC-13** 临界草案：模拟提及率 < 30% 连续 2 周 → 策略更新草案生成
- [ ] **AC-14** content_asset_id：publish_tasks 关联 content_assets
- [ ] **AC-15** thin KB 门槛：KB 不足→方案包黄条提示，不硬生成
- [ ] **AC-16** 机器审 11 项：A1-A11 全部生效
- [ ] **AC-17** pipeline 容错：单个 engine 超时 → skip，其余继续

### 2.2 视觉 UI 验收（对标 G-L2-设计规范.md）

- [ ] 所有页面使用 Element Plus 组件，无裸 HTML 替代
- [ ] 色值统一用 `var(--el-color-*)`，不写死 HEX
- [ ] 加载/空/报错状态：`v-loading` + `el-empty` + `el-result`
- [ ] 按钮规范：主/次/危险/禁用态正确使用
- [ ] 页面切换有 fade 过渡

### 2.3 代码架构验收（对标 G-L2-架构设计说明书.md）

- [ ] 目录结构符合约定，无违规新建文件夹
- [ ] API 调用统一走 `frontend/src/api/` Axios 实例
- [ ] 后端全部通过 Pydantic v2 schemas 校验
- [ ] 未破坏已有接口和数据库表字段
- [ ] 无 `console.log`、废弃注释、硬编码常量

### 2.4 非功能验收

- [ ] **NFR-01** 页面首屏 < 3s（PC Chrome，3G 降速）
- [ ] **NFR-02** API P95 < 2s（LLM 调用除外）
- [ ] **NFR-03** 4 EngineAdapter 均可调通
- [ ] **NFR-04** Celery worker 正常运行，失败重试生效
- [ ] **NFR-05** Sentry 错误上报正常
- [ ] **NFR-06** LangSmith trace 可查

---

## 三、回滚触发条件

### 3.1 阻塞上线（必须修）

| # | 问题 |
|---|------|
| B1 | 用户 A 能访问用户 B 的企业数据（跨租户泄露） |
| B2 | fact_verify 被绕过，未引用 Fact 的内容可发布 |
| B3 | JWT 鉴权失效，未登录可调 API |
| B4 | 发布到外部渠道时泄露其他租户内容 |
| B5 | 数据库迁移不可逆，执行后无法回滚 |
| B6 | 核心接口报错率 > 1% |

### 3.2 降级上线（可修后补）

| # | 问题 |
|---|------|
| D1 | 单个 engine adapter 不可用（其余 engine 正常） |
| D2 | Faiss 服务启动失败（降级为 in-memory 去重） |
| D3 | 小红书 SEMI 包少字段（补字段） |
| D4 | 效果舱流量数据延迟（异步刷新可接受） |

---

## 四、分层回滚操作

### 4.1 代码层回滚

```bash
# 回滚到基线
git reset --hard 13fdcb4
git clean -fd

# 或 revert 指定 commit
git revert <commit-hash>
```

### 4.2 数据库回滚

```bash
cd backend

# 回滚最新迁移
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision>
```

**规则：**
- 仅新增表 → `DROP TABLE`
- 仅新增字段 → `ALTER TABLE DROP COLUMN`
- 反向脚本存放：`backend/alembic/versions/revert/`

### 4.3 服务回滚

```bash
docker compose down
docker compose -f docker-compose.prev.yml up -d
```

### 4.4 回滚后验证

1. 登录→开店向导跑通
2. 已发布内容可正常查看
3. 监测历史数据不丢
4. 新企业注册正常

---

## 五、上线清单

- [ ] 4 份规范文档（PRD/ARCHITECTURE/DESIGN/ROLLBACK）已评审
- [ ] AC-01 ~ AC-17 全部通过
- [ ] 安全自检：跨租户 403、JWT 过期、托管页 XSS sanitize + CSP
- [ ] 数据库备份就绪
- [ ] `.env` 生产 key 已脱敏
- [ ] Sentry DSN / LangSmith project key 已配置
- [ ] 种子数据 `seed_beauty_enterprise` 可一键执行

---

## 六、回滚历史归档

上线稳定 7 天后，复制本文档至 `docs/rollback-history/rollback-feat-mvp-beauty-local-v1.md`。

---

*ROLLBACK v1.0 · 对齐 AC-01～AC-17*
