# GEO 登录注册逻辑文档

> 参考 TalentFlow `auth_flow.md` 结构编写。GEO 为多租户（Multi-tenant，多企业隔离）SaaS：注册时同时创建 **Enterprise（企业）** 与 **User（用户）**，登录以 **邮箱** 为账号。

---

## 一、整体架构

### 模块职责划分

| 模块 | 文件路径 | 职责描述 |
|------|----------|----------|
| **API 接口层** | `app/api/v1/auth.py` | 对外暴露注册/登录/me/refresh 接口 |
| **安全模块** | `app/core/security.py` | 密码哈希、JWT 生成/解析、OAuth2 依赖、权限校验 |
| **业务服务层** | `app/service/auth_service.py` | 注册、登录、发 Token、成员邀请等企业用户逻辑 |
| **依赖导出（兼容）** | `app/api/deps/auth.py` | 从 `security.py` re-export，供路由 `Depends` 使用 |
| **数据模型** | `app/models/auth.py` | `Enterprise` / `User` ORM 模型 |
| **数据结构** | `app/schemas/auth.py` | 请求/响应 Pydantic Schema + 角色层级 |
| **配置管理** | `app/core/config.py` | JWT 密钥、过期时间、平台管理员白名单 |

### 与 TalentFlow 的主要差异

| 维度 | TalentFlow | GEO |
|------|------------|-----|
| 登录账号 | `username` | `email` |
| 数据访问 | `crud/crud.py` | `UserService` / `EnterpriseService` |
| 租户模型 | 单用户表 | `Enterprise` + `User`（一对多） |
| 注册产物 | 仅 User | Enterprise + owner User + 自动发 Token |
| deps 位置 | `app/core/deps.py` | 已合并进 `app/core/security.py` |
| 响应包装 | 直接返回 Schema | `ResponseModel[T]` 统一包装 |

---

## 二、注册流程

### 2.1 流程图

```
客户端请求 POST /api/v1/auth/register
         │
         ▼
┌─────────────────────┐
│  1. 接收请求参数    │  UserCreate (email, password, enterprise_name, industry…)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. 检查邮箱唯一性  │  UserService.get_by_email()
└─────────┬───────────┘
          │
          ▼ (邮箱已存在)
┌─────────────────────┐     ┌─────────────────────────┐
│  抛出 HTTP 400      │────▶│  "该邮箱已注册"         │
└─────────────────────┘     └─────────────────────────┘
          │
          ▼ (邮箱不存在)
┌─────────────────────┐
│  3. 创建 Enterprise │  EnterpriseService.create()
│  status=active      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  4. 密码哈希        │  security.get_password_hash() — Argon2
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  5. 创建 owner User │  role="owner", enterprise_id=新企业 ID
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  6. 签发 JWT        │  UserService.issue_token()
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  7. 返回 TokenPayload│  ResponseModel { access_token, user, expires_in }
└─────────────────────┘
```

### 2.2 核心代码解析

**注册接口** (`app/api/v1/auth.py`):

```python
@router.post("/register", response_model=ResponseModel[TokenPayload])
def register(data: UserCreate, db: Session = Depends(get_db)):
    try:
        enterprise, user = UserService.register(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = UserService.issue_token(user)
    return ResponseModel(data=token, message="注册成功")
```

**注册业务** (`app/service/auth_service.py`):

```python
def register(db: Session, data: UserCreate) -> Tuple[Enterprise, User]:
    if UserService.get_by_email(db, data.email):
        raise ValueError("该邮箱已注册")
    enterprise = EnterpriseService.create(db, EnterpriseCreate(...))
    user = User(
        enterprise_id=enterprise.id,
        email=data.email.lower().strip(),
        hashed_password=get_password_hash(data.password),
        role="owner",
        is_active=True,
        ...
    )
    db.add(user)
    db.commit()
    return enterprise, user
```

---

## 三、登录流程

GEO 提供两种登录入口，底层共用 `UserService.authenticate()`。

### 3.1 OAuth2 表单登录（Swagger / 标准客户端）

```
客户端请求 POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
         │
         ▼
┌─────────────────────┐
│  1. 接收 OAuth2 表单│  username 字段填邮箱，password 填密码
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. 查询用户        │  UserService.get_by_email()
└─────────┬───────────┘
          │
          ▼ (用户不存在 / 已禁用 / 密码错误)
┌─────────────────────┐     ┌─────────────────────────┐
│  抛出 HTTP 401      │────▶│  "邮箱或密码错误"       │
└─────────────────────┘     └─────────────────────────┘
          │
          ▼ (验证通过)
┌─────────────────────┐
│  3. 更新 last_login │  user.last_login_at = now()
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  4. 签发 JWT        │  UserService.issue_token()
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  5. 返回 TokenPayload│  ResponseModel { access_token, user, expires_in }
└─────────────────────┘
```

### 3.2 JSON 登录（前端常用）

```
POST /api/v1/auth/login/json-login
Body: { "email": "...", "password": "..." }
         │
         ▼
（与 3.1 步骤 2–5 相同）
```

### 3.3 核心代码

**OAuth2 登录** (`app/api/v1/auth.py`):

```python
@router.post("/login", response_model=ResponseModel[TokenPayload])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    data = UserLogin(email=form_data.username, password=form_data.password)
    user = UserService.authenticate(db, data)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误", ...)
    return ResponseModel(data=UserService.issue_token(user))
```

**认证逻辑** (`app/service/auth_service.py`):

```python
def authenticate(db: Session, data: UserLogin) -> Optional[User]:
    user = UserService.get_by_email(db, data.email)
    if not user or not user.is_active:
        return None
    if not verify_password(data.password, user.hashed_password):
        return None
    user.last_login_at = datetime.utcnow()
    db.commit()
    return user
```

---

## 四、密码验证机制

### 4.1 密码哈希算法

使用 **Argon2**（目前主流的安全密码哈希算法之一）。

**配置位置** (`app/core/security.py`):

```python
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
```

依赖：`argon2-cffi`（见 `requirements.txt`）。

### 4.2 密码处理流程

| 阶段 | 操作 | 函数 | 文件位置 |
|------|------|------|----------|
| **注册/邀请** | 明文 → 哈希 | `get_password_hash(password)` | `app/core/security.py` |
| **登录** | 明文 vs 哈希 | `verify_password(plain, hashed)` | `app/core/security.py` |

### 4.3 安全特性

| 特性 | 说明 |
|------|------|
| **加盐处理** | Argon2 自动生成随机盐，同一密码哈希值不同 |
| **内存/时间硬** | 可配置计算成本，增加暴力破解难度 |
| **统一错误提示** | 不区分「邮箱不存在」与「密码错误」 |
| **字段命名** | 数据库存 `hashed_password`，不存明文 |

---

## 五、JWT Token 机制

### 5.1 Token 结构

```
Header.Payload.Signature
```

**Payload 内容**：

| 字段 | 说明 | 示例 |
|------|------|------|
| `exp` | 过期时间（UTC） | `2026-07-08T12:00:00` |
| `sub` | 主题（用户 ID） | `1` |
| `type` | Token 类型 | `access` |

> 兼容旧 Token：`type` 缺失时仍视为 access token。

### 5.2 Token 生成

**核心代码** (`app/core/security.py`):

```python
def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

**封装返回** (`UserService.issue_token`):

```python
TokenPayload(
    access_token=token,
    token_type="bearer",
    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    user=UserResponse.model_validate(user),
)
```

### 5.3 配置参数

| 参数 | 配置位置 | 默认值 |
|------|----------|--------|
| `SECRET_KEY` | `.env` | `change-me-in-production-please` |
| `ALGORITHM` | `app/core/config.py` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `app/core/config.py` | `1440`（24 小时） |

### 5.4 Token 刷新

```
POST /api/v1/auth/refresh
Authorization: Bearer <valid_token>
         │
         ▼
get_current_user 校验通过后重新 issue_token
```

---

## 六、请求认证（Token 校验）

鉴权逻辑位于 **`app/core/security.py`**（原 `app/api/deps/auth.py` 已合并，路由仍可通过 `from app.api.deps import get_current_user` 引用）。

### 6.1 流程

```
客户端请求（Authorization: Bearer <token>）
         │
         ▼
┌─────────────────────┐
│  1. 提取 Token      │  oauth2_scheme (OAuth2PasswordBearer)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. 解码 Token      │  decode_token() → jwt.decode()
└─────────┬───────────┘
          │
          ▼ (解码失败 / type 非 access / 用户不存在 / 已禁用)
┌─────────────────────┐     ┌─────────────────────────┐
│  抛出 HTTP 401      │────▶│  "未认证或认证已过期"   │
└─────────────────────┘     └─────────────────────────┘
          │
          ▼ (校验通过)
┌─────────────────────┐
│  3. 返回 User ORM   │  供路由 / Service 使用
└─────────────────────┘
```

### 6.2 核心代码

**依赖函数** (`app/core/security.py`):

```python
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

def get_current_user_or_none(token, db) -> Optional[User]:
    payload = decode_token(token)
    if payload.get("type") not in (None, "access"):
        return None
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return user if user and user.is_active else None

def get_current_user(current_user = Depends(get_current_user_or_none)) -> User:
    if not current_user:
        raise HTTPException(status_code=401, detail="未认证或认证已过期", ...)
    return current_user
```

### 6.3 权限控制

#### 企业内角色（RBAC，Role-Based Access Control，基于角色的访问控制）

| 角色 | 层级 | 典型权限 |
|------|------|----------|
| `owner` | 100 | 企业最高权限，可管理成员 |
| `admin` | 80 | 企业管理 |
| `editor` | 50 | 内容/KB 写入 |
| `member` | 30 | 普通成员 |
| `viewer` | 10 | 只读 |

层级比较函数：`role_can_manage(actor_role, target_role)`（`app/schemas/auth.py`）。

**权限依赖** (`app/core/security.py`):

| 函数 | 用途 |
|------|------|
| `require_role("owner", "admin")` | 限定企业角色 |
| `require_enterprise_owner_or_admin` | owner / admin 快捷校验 |
| `require_platform_admin` | 平台管理端 `/api/v1/admin/*` |

#### 平台管理员

满足任一条件即可访问 admin 路由：

1. `user.role == "platform_admin"`
2. `user.email` 在 `.env` 的 `PLATFORM_ADMIN_EMAILS` 白名单中

---

## 七、成员邀请（注册延伸）

企业 owner/admin 可邀请成员，不走公开注册接口。

```
POST /api/v1/user/enterprise/members/invite
         │
         ▼
role_can_manage(actor.role, invite.role) 校验
         │
         ▼
邮箱未占用 → 创建 User（临时密码哈希）→ 被邀请者自行注册/改密登录
```

> MVP 阶段邀请用户若邮箱已存在会报错「该邮箱已加入企业，可直接登录」。

---

## 八、数据结构定义

### 8.1 注册输入

**UserCreate** (`app/schemas/auth.py`):

| 字段 | 类型 | 说明 |
|------|------|------|
| `email` | EmailStr | 登录账号（全局唯一） |
| `password` | str | 6–128 位 |
| `full_name` | str | 联系人姓名 |
| `enterprise_name` | str | 企业名称 |
| `industry` | str | 默认 `beauty_local` |
| `license_no` | str? | 营业执照号（可选） |
| `phone` / `avatar` | str? | 可选 |

### 8.2 登录输入

**UserLogin**: `{ email, password }`

OAuth2 表单：`username` = 邮箱，`password` = 密码。

### 8.3 登录/注册响应

**TokenPayload**:

```python
class TokenPayload(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int          # 秒
    user: UserResponse
```

外层统一包装：`ResponseModel[TokenPayload]` → `{ code, message, data }`。

### 8.4 数据库模型

**Enterprise** (`app/models/auth.py` — `enterprises` 表):

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | 企业 ID（租户 ID） |
| `name` | String(200) | 企业名称 |
| `industry` | String(50) | 行业包 |
| `license_no` | String(100) | 执照号 |
| `status` | String(20) | 默认 `active` |
| `plan` | String(30) | 默认 `mvp` |
| `settings` | JSON | 扩展配置（如地址） |
| `kb_updated_at` | DateTime | KB 最后更新时间 |

**User** (`app/models/auth.py` — `users` 表):

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 用户 ID |
| `enterprise_id` | Integer | FK → enterprises | 所属企业 |
| `email` | String(200) | UNIQUE | 登录账号 |
| `hashed_password` | String(255) | NOT NULL | Argon2 哈希 |
| `full_name` | String(100) | NOT NULL | 姓名 |
| `role` | String(30) | INDEX | owner/admin/editor/member/viewer |
| `is_active` | Boolean | DEFAULT true | 是否启用 |
| `last_login_at` | DateTime | | 最近登录 |

---

## 九、API 路由一览

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 无 | 注册企业 + owner |
| POST | `/api/v1/auth/login` | 无 | OAuth2 表单登录 |
| POST | `/api/v1/auth/login/json-login` | 无 | JSON 登录 |
| GET | `/api/v1/auth/me` | Bearer | 当前用户信息 |
| POST | `/api/v1/auth/refresh` | Bearer | 刷新 Token |

用户端 / 管理端业务路由分别挂载在 `/api/v1/user/*` 与 `/api/v1/admin/*`，均需 Bearer Token（admin 另需平台管理员权限）。

**横切共用**（类比 TalentFlow `skills` / `tasks`，挂 v1 根目录）：

| 前缀 | 说明 |
|------|------|
| `/api/v1/llm/*` | LLM 引擎列表、对话、Embedding |
| `/api/v1/agent/*` | Agent 任务创建/查询/进度 |

---

## 十、安全最佳实践

| 实践 | 实现位置 | 说明 |
|------|----------|------|
| **密码哈希** | `security.py` | Argon2 + argon2-cffi |
| **统一错误提示** | `auth.py` / `auth_service.py` | 不泄露账号是否存在 |
| **Token 过期** | `config.py` | 默认 24h，生产可调短 |
| **租户隔离** | 各 Service | 查询带 `enterprise_id` |
| **平台管理员** | `require_platform_admin` | 角色 + 邮箱白名单双通道 |
| **HTTPS** | 部署层 | 生产环境强制 HTTPS |
| **密钥管理** | `.env` | `SECRET_KEY` 不提交仓库 |

---

## 十一、前端对接要点

| 场景 | 调用 |
|------|------|
| 注册 | `POST /api/v1/auth/register` — body 见 `UserCreate` |
| 登录 | `POST /api/v1/auth/login/json-login` 或 OAuth2 `/login` |
| 持久化 | 存 `data.access_token`，请求头 `Authorization: Bearer …` |
| 当前用户 | `GET /api/v1/auth/me` |
| LLM / Agent | `/api/v1/llm/*`、`/api/v1/agent/*`（横切共用） |
| 业务 API | 前缀 `/api/v1/user/...`（舱1/2/3 按域） |

前端封装：`frontend/src/api/auth.ts`。
