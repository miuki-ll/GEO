# GEO 安全规范

> **版本**：v2.1 | **日期**：2026-07-16
> **关联**：[G-L2-架构设计说明书.md](G-L2-架构设计说明书.md) · [G-L4-部署运维手册.md](G-L4-部署运维手册.md)

---

## 1. 安全架构总览

```
┌─────────────────────────────────────────────────────────┐
│                      安全防线                             │
│                                                          │
│  第一层 · 认证     JWT + bcrypt/argon2 + 过期24h          │
│  第二层 · 授权     租户隔离 enterprise_id + RBAC 4角色     │
│  第三层 · 传输     HTTPS + API Key 平台侧注入               │
│  第四层 · 存储     AES-256加密凭证 + pg SSL + 托管页 CSP   │
│  第五层 · Agent    ToolRegistry 白名单 · 禁止写操作        │
│  第六层 · 审计     approval_log + agent_traces + Sentry   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 认证与授权

### 2.1 JWT

| 配置 | 值 |
|------|-----|
| 算法 | HS256 |
| 过期 | 24 小时 |
| Payload | `{ user_id, enterprise_id, role, exp }` |
| 刷新 | 不支持 refresh token（MVP）；过期需重新登录 |

### 2.2 密码

```
注册：argon2-cffi 哈希存储（优先） → bcrypt 降级
强度：最少 8 位，含大小写+数字+特殊字符
```

### 2.3 租户隔离

```python
# 所有 API 请求强制注入 enterprise_id
# Service 层强制过滤
def get_current_user(token: str) -> User:
    payload = decode_jwt(token)
    return User(id=payload["user_id"], enterprise_id=payload["enterprise_id"])

# 跨租户访问拦截
if resource.enterprise_id != current_user.enterprise_id:
    raise HTTPException(403, "无权访问此资源")
```

### 2.4 RBAC 四角色

| 角色 | 权限 |
|------|------|
| **Owner** | 全部：入驻/诊断/方案包/内容审核/发布/看效果/企业设置/修改主攻AI |
| **Admin** | 运营：除删除企业和修改企业名外，其余同 Owner |
| **Editor** | 内容：审稿/改稿/看诊断/看效果 |
| **Viewer** | 只读：看报告/看效果舱 |

---

## 3. 数据安全

### 3.1 传输加密

```
- 全站 HTTPS（生产 ALB + ACM）
- API Key 仅通过环境变量注入，不在前端暴露
- 渠道凭证（小红书/知乎密码） AES-256 加密存储
```

### 3.2 存储加密

```
- PostgreSQL: 生产启用 SSL 连接
- 密码字段: argon2-cffi / bcrypt 哈希
- 渠道凭证: AES-256-CBC 加密，密钥存于 SECRET_KEY
```

### 3.3 托管页安全

```
- HTML sanitize（发布前）：strip <script> / <iframe> / on* 事件
- Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline'
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Schema.org JSON-LD：仅允许预定义类型
```

---

## 4. Agent 安全

### 4.1 ToolRegistry 白名单

```
允许（只读）：
  - kb_fetch(fact_refs)     拉取 KB Fact
  - search_engine(query)    搜索引擎查询
  - page_fetch(url)         白名单 URL 抓取
  - faiss_search(query)     向量检索
  - engine_chat(prompt)     LLM 对话

禁止：
  - write_fact / update_fact / delete_fact
  - auto_confirm / auto_publish
  - write_db / execute_sql
```

### 4.2 ReAct 约束

```
- max_steps ≤ 5（competitor_graph / gap_graph）
- 正文 Skill 固定链（无 ReAct · 2次调用封顶）
- 所有 Agent 调用经过 LLM Gateway（统一配额+熔断）
```

---

## 5. API 安全

### 5.1 限流

```
全局：100 请求/分钟/IP
按端点：
  POST /onboarding/run:   5 次/小时/租户
  LLM 相关:              30 次/分钟/租户
  GET 列表:              60 次/分钟/租户
```

### 5.2 输入校验

```
- 所有请求体走 Pydantic v2 校验（extra=forbid）
- SQL 注入防护：SQLAlchemy ORM 参数化查询
- XSS 防护：用户输入 HTML sanitize（bleach）
- 文件上传：限 10MB · 仅允许 txt/csv/json
```

### 5.3 CORS

```
开发：allow_origins=["http://localhost:5173"]
生产：allow_origins=["https://app.geo-platform.com"]
```

---

## 6. 基础设施安全

### 6.1 Docker

```
- 非 root 用户运行容器
- 镜像扫描（docker scout / trivy）
- .env 文件不提交 Git（已加入 .gitignore）
- SECRET_KEY 随机生成，不硬编码
```

### 6.2 网络安全

```
- 防火墙：仅开放 80/443/22（IP 白名单）
- pg 端口不对外暴露（仅 Docker 内网）
- Redis 端口不对外暴露 + 密码保护
```

---

## 7. 合规

### 7.1 数据保护

```
- 用户数据不出境（仅国内模型 API · 可选「仅国内模型」租户开关 V1.1）
- RawInputs 保留期可配置（默认 180 天）
- 用户可请求删除全部数据（V1.1）
```

### 7.2 AI 生成标识

```
- 所有 AI 生成内容标注：「本文由 AI 辅助生成，经人工审核确认」
- 广告法合规：禁词拦截（最好/第一/100%/国家级/纯天然等）
- 生美行业合规：禁止医疗功效表述
```

### 7.3 审计日志

```
- approval_log: 所有人闸门操作（确认/打回）+ 操作人 + 时间戳
- agent_traces: 所有 Agent 调用（graph/step/action/observation/tokens）
- API 访问日志: Sentry 采集 + Nginx access log
```

---

## 8. 安全验收清单

| # | 检查项 | 方法 |
|---|--------|------|
| S-01 | 跨租户访问 403 | 用 A 的 Token 访问 B 的数据 |
| S-02 | 未登录访问 401 | 不带 Token 调 API |
| S-03 | JWT 过期 401 | 用过期 Token 调 API |
| S-04 | 密码哈希不可逆 | 检查数据库密码字段非明文 |
| S-05 | 托管页 XSS 过滤 | 提交含 `<script>` 的 HTML → 被 sanitize |
| S-06 | Agent 写操作拒绝 | 调用 write_fact → 报错 |
| S-07 | 限流 429 | 1 秒内 100 次请求 → 429 |
| S-08 | .env 不入库 | `git ls-files | grep .env` → 无结果 |
| S-09 | AI 生成标识存在 | 所有生成内容含标识文案 |
| S-10 | 禁词拦截生效 | 提交含「最好」的文案 → 拒发 |

---

*安全规范 v2.1 · 6 层防线 · 10 项验收*
