# GEO API 契约

> **版本**：v2.1 | **日期**：2026-07-16
> **关联**：[G-L2-架构设计说明书.md](G-L2-架构设计说明书.md) · [G-L1-需求规格说明书.md](G-L1-需求规格说明书.md)

---

## 0. 统一规范

### 0.1 返回格式

```json
// 成功
{ "code": 0, "data": {...}, "msg": "ok" }

// 列表
{ "code": 0, "data": { "items": [...], "total": 100, "page": 1, "page_size": 20 }, "msg": "ok" }

// 失败
{ "code": 400, "data": null, "msg": "参数错误" }
```

### 0.2 状态码

| code | 含义 |
|------|------|
| 0 | 成功 |
| 400 | 参数错误 |
| 401 | 未登录 |
| 403 | 无权限（跨租户） |
| 404 | 资源不存在 |
| 422 | Pydantic 校验失败 |
| 429 | 限流 |
| 500 | 服务端错误 |

### 0.3 鉴权

```
Header: Authorization: Bearer <JWT>
JWT payload: { user_id, enterprise_id, role, exp }
过期: 24h
所有 /api/v1/user/* 需 JWT（除 /api/v1/auth/*）
```

### 0.4 分页

```
Query: ?page=1&page_size=20
Response: { items: T[], total: int, page: int, page_size: int }
默认 page=1, page_size=20, max page_size=100
```

---

## 1. Auth 模块

### POST /api/v1/auth/register

```
Request:
{
  "email": "owner@example.com",
  "password": "Admin@12345",
  "full_name": "张美丽",
  "phone": "13800138000",
  "role": "owner",
  "enterprise_name": "倾城美业",
  "industry": "beauty_local",
  "city": "上海市",
  "district": "静安区"
}

Response 200:
{
  "code": 0,
  "data": {
    "enterprise": { "id": 1, "name": "倾城美业", "industry": "beauty_local" },
    "user": { "id": 1, "email": "owner@example.com", "role": "owner" },
    "token": "eyJ..."
  }
}
```

### POST /api/v1/auth/login

```
Request:
{ "email": "owner@example.com", "password": "Admin@12345" }

Response 200:
{ "code": 0, "data": { "token": "eyJ...", "user": { "id": 1, "email": "...", "role": "owner", "enterprise_id": 1 } } }
```

### GET /api/v1/auth/me

```
Header: Authorization: Bearer <JWT>

Response 200:
{ "code": 0, "data": { "id": 1, "email": "...", "full_name": "...", "role": "owner", "enterprise_id": 1, "enterprise_name": "倾城美业" } }
```

---

## 2. Enterprise 模块

### GET /api/v1/user/enterprise

```
Response 200:
{
  "code": 0,
  "data": {
    "id": 1, "name": "倾城美业", "industry": "beauty_local",
    "industry_pack": "beauty_local", "license_no": "...",
    "status": "active", "plan": "basic",
    "target_engines": ["doubao", "deepseek"],
    "kb_updated_at": "2026-07-16T10:00:00Z"
  }
}
```

### PUT /api/v1/user/enterprise

```
Request:
{
  "name": "倾城美业 · XX路店",
  "target_engines": ["doubao", "kimi"]   // 修改主攻AI → 监测联动切换
}

Response 200:
{ "code": 0, "data": { "id": 1, "target_engines": ["doubao", "kimi"] } }
```

---

## 3. 知识库模块

### GET /api/v1/user/kb/facts

```
Query: ?category=qualification&page=1&page_size=20

Response 200:
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1, "title": "卫生与资质 - 1", "content": "门店持有《卫生许可证》...",
        "source_type": "official", "source_ref": "https://...",
        "category": "qualification", "tags": ["合规", "资质"], "verified": true
      }
    ],
    "total": 20, "page": 1, "page_size": 20
  }
}
```

### POST /api/v1/user/kb/facts

```
Request:
{
  "title": "补水管理项目价格",
  "content": "补水管理 298-498 元/次，含 VISIA 检测 + B5 精华导入",
  "source_type": "official",
  "category": "price",
  "tags": ["价格", "补水"],
  "verified": true
}

Response 201:
{ "code": 0, "data": { "id": 21 } }
```

### GET /api/v1/user/kb/faqs

### POST /api/v1/user/kb/faqs

```
Request:
{
  "question": "敏感肌能不能做皮肤管理？",
  "answer": "可以。敏感肌先做 VISIA 检测...",
  "source_ref": "kb_fact:1",
  "fact_refs": [1, 5, 8]
}
```

### GET /api/v1/user/kb/signals

---

## 4. 入驻 & 诊断模块（舱1）

### POST /api/v1/user/onboarding/run

```
Request:
{
  "target_engines": ["doubao", "deepseek"],
  "industry": "beauty_local",
  "brand": { "name": "倾城美业", "differentiator": "透明价格 + 1v1客制化" },
  "stores": [
    { "name": "XX路店", "address": "静安区XX路88号", "lat": 31.23, "lng": 121.45,
      "phone": "021-12345678", "hours": "10:00-22:00" }
  ],
  "services": [
    { "name": "敏感肌修护", "price_range": "298-498元", "duration": "60分钟", "target_group": "敏感肌人群" },
    { "name": "深度补水", "price_range": "198-398元", "duration": "45分钟", "target_group": "所有肤质" }
  ],
  "target_customers": ["敏感肌人群", "白领女性", "抗衰熟龄"],
  "competitors": [
    { "name": "XX美容连锁", "url": "https://www.dianping.com/shop/xxx" }
  ],
  "differentiator": "透明价格 + 成分公开 + 1v1客制化方案",
  "raw_inputs": "客户常问：敏感肌能做吗？会不会越做越敏感？..."
}

Response 202:
{ "code": 0, "data": { "task_id": "a1b2c3d4", "status": "pending" } }
```

### GET /api/v1/user/onboarding/status/{task_id}

```
Response 200 (SSE stream):
data: {"step": "DIAGNOSE", "progress_pct": 25, "progress_message": "DIAGNOSE done"}
data: {"step": "PAIN", "progress_pct": 50, "progress_message": "PAIN done"}
data: {"step": "PERSONA", "progress_pct": 75, "progress_message": "PERSONA done"}
data: {"step": "COMPETITOR", "progress_pct": 100, "progress_message": "COMPETITOR done"}
data: {"progress_pct": 100, "next_route": "/strategy-pack?draft=1"}
```

### GET /api/v1/user/diagnosis/{id}

```
Response 200:
{
  "code": 0,
  "data": {
    "id": 1,
    "engine_code": "doubao",
    "probe_prompts": ["静安寺附近皮肤管理推荐", "敏感肌能不能做皮肤管理", ...],
    "brand_mention_rate": 0.05,
    "avg_rank": null,
    "hallucination_rate": 0.0,
    "competitor_occupancy": {
      "XX美容连锁": 0.40,
      "社区单店": 0.20
    },
    "source_map": {
      "rankings": [
        { "domain": "dianping.com", "count": 12, "weight": 0.35 },
        { "domain": "zhihu.com", "count": 8, "weight": 0.24 },
        { "domain": "sohu.com", "count": 6, "weight": 0.18 }
      ],
      "gaps": ["今日头条", "小红书"]
    },
    "track": "blank",
    "track_strategy": "优先布局敏感肌修护类场景问句",
    "competitor_analysis": [
      {
        "name": "XX美容连锁", "type": "chain",
        "strengths": ["品牌知名度", "多家门店"],
        "weaknesses": ["客制化差", "推销感强"],
        "differentiation": "本地化定制 + 1v1方案"
      }
    ]
  }
}
```

---

## 5. 词库模块（舱1·前半）

### GET /api/v1/user/keywords

```
Query: ?layer=选型层&source=探针反推&page=1&page_size=50

Response 200:
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1, "keyword": "静安寺皮肤管理推荐", "layer": "选型层",
        "source": "LLM生成", "lbs_tags": ["静安区", "静安寺商圈"],
        "created_at": "2026-07-16T10:00:00Z"
      }
    ],
    "total": 45, "page": 1, "page_size": 50
  }
}
```

### POST /api/v1/user/keywords

```
Request:
{
  "keyword": "敏感肌修护哪家不推销",
  "layer": "痛点层",
  "source": "手动",
  "lbs_tags": ["静安区"]
}

Response 201:
{ "code": 0, "data": { "id": 46 } }
```

### PUT /api/v1/user/keywords/{id}

### DELETE /api/v1/user/keywords/{id}

### POST /api/v1/user/keywords/generate

```
Request: {}  // 触发四源汇聚重新生成

Response 202:
{ "code": 0, "data": { "task_id": "kw-gen-001" } }
```

---

## 6. 方案包模块（舱2）

### GET /api/v1/user/strategy-pack/draft

```
Response 200:
{
  "code": 0,
  "data": {
    "id": 1,
    "persona": {
      "buyer_personas": [
        { "role": "静安寺白领女性", "age_range": [25,35], "pain_tags": ["敏感肌","怕推销","午休短"],
          "decision_factors": ["口碑","资质","距离","风格"], "trust_triggers": ["VISIA报告","评价带图"] }
      ],
      "content_layout_plan": [
        { "persona": "敏感肌白领", "content_type": "FAQ+场景推荐", "channel": "小红书+知乎", "cta": "预约小程序" }
      ]
    },
    "competitors": {
      "profiles": [
        { "name": "XX美容连锁", "type": "chain", "ai_mention_rate": 0.40,
          "strengths": ["品牌知名度"], "weaknesses": ["客制化差"], "differentiation": "本地化定制" }
      ],
      "differentiation_brief": "你的差异化：透明价格+成分公开+客制化方案",
      "content_gaps": ["缺少敏感肌修护FAQ", "未覆盖换季护理场景", "没有对比评测"]
    },
    "scenarios": {
      "candidates": [
        { "id": "c1", "user_query": "敏感肌能不能做皮肤管理", "intent": "项目咨询", "channel": "hosted", "skill": "faq" },
        { "id": "c2", "user_query": "静安寺附近做脸哪家不推销", "intent": "到店决策", "channel": "xiaohongshu", "skill": "article" },
        { "id": "c3", "user_query": "XX皮肤管理和YY美容院怎么选", "intent": "选型对比", "channel": "zhihu", "skill": "comparison" }
      ],
      "recommended_count": 3,
      "max": 5
    },
    "channels": [
      { "name": "AI托管页", "model_weight": 0.40, "probe_weight": 0.10, "mixed_weight": 0.28, "scenario_count": 1 },
      { "name": "小红书", "model_weight": 0.25, "probe_weight": 0.05, "mixed_weight": 0.17, "scenario_count": 1 },
      { "name": "知乎", "model_weight": 0.10, "probe_weight": 0.15, "mixed_weight": 0.12, "scenario_count": 1 }
    ],
    "keywords": { "layers": { "选型层": [...], "场景层": [...], "痛点层": [...], "认知层": [...] } },
    "kb_freshness": { "warning": false, "updated_at": "2026-07-16T10:00:00Z" }
  }
}
```

### POST /api/v1/user/strategy-pack/confirm

```
Request:
{
  "selected_scenarios": ["c1", "c2"],
  "channel_overrides": { "xiaohongshu": 1 },
  "persona_confirmed": true,
  "competitor_confirmed": true
}

Response 200:
{ "code": 0, "data": { "strategy_pack_id": 1, "status": "confirmed", "next_route": "/content/drafts" } }
```

---

## 7. 内容模块（舱2）

### GET /api/v1/user/content/drafts

```
Query: ?status=ready&page=1&page_size=20

Response 200:
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1, "scenario_id": 1, "channel": "hosted", "skill": "faq",
        "title": "敏感肌能不能做皮肤管理？",
        "body": "可以。敏感肌先做VISIA检测...",
        "fact_refs": [1, 5, 8],
        "machine_review": { "fact_verify": true, "forbidden_words": true, "cross_validation": true, "entity_consistency": true, "rag_readability": true },
        "status": "ready"
      }
    ],
    "total": 3, "page": 1, "page_size": 20
  }
}
```

> **机审五键语义（TD-04 定稿）**：每键 `true` = 该项通过；`forbidden_words: true` 表示**未命中**禁词（通过），`false` 表示命中未通过。与其余四键同向，可用 `all(machine_review.values())` 判断整单是否过机审。
### POST /api/v1/user/content/drafts/{id}/approve

```
Response 200:
{ "code": 0, "data": { "id": 1, "status": "ready" } }
```

### POST /api/v1/user/content/drafts/bulk-approve

```
Request:
{ "ids": [1, 2, 3] }

Response 200:
{ "code": 0, "data": { "approved": 3, "failed": [], "next_route": "/publish/tasks" } }
```

### POST /api/v1/user/content/drafts/{id}/reject

```
Request:
{ "reason": "价格需要更新为298元" }

Response 200:
{ "code": 0, "data": { "id": 1, "status": "draft" } }
```

---

## 8. 发布模块（舱3）

### GET /api/v1/user/publish/tasks

```
Query: ?status=pending&page=1&page_size=20

Response 200:
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1, "content_asset_id": 1, "channel": "hosted", "mode": "AUTO",
        "status": "pending", "scheduled_at": null
      },
      {
        "id": 2, "content_asset_id": 2, "channel": "xiaohongshu", "mode": "SEMI",
        "status": "pending", "export_package": {
          "title": "...", "body": "...", "tags": ["皮肤管理","敏感肌"],
          "cover_hint": "使用VISIA检测过程图", "steps": ["打开小红书APP","粘贴文案","上传图片","发布"]
        }
      }
    ],
    "total": 3
  }
}
```

### POST /api/v1/user/publish/run

```
Request:
{ "task_ids": [1, 2] }

Response 202:
{ "code": 0, "data": { "started": 2 } }
```

### GET /api/v1/user/publish/tasks/{id}

```
Response 200:
{
  "code": 0,
  "data": {
    "id": 1, "content_asset_id": 1, "channel": "hosted",
    "mode": "AUTO", "status": "published",
    "published_url": "https://hosted.geo.local/p/xxx",
    "published_at": "2026-07-16T14:00:00Z"
  }
}
```

---

## 9. 监测模块（舱3）

### GET /api/v1/user/monitor/profiles

```
Response 200:
{
  "code": 0,
  "data": {
    "core": { "id": 1, "pool_type": "Core", "engine_codes": ["doubao"], "prompt_count": 22, "schedule": "weekly" },
    "probe": { "id": 2, "pool_type": "Probe", "engine_codes": ["doubao"], "prompt_count": 8, "schedule": "weekly" }
  }
}
```

### GET /api/v1/user/monitor/results

```
Query: ?baseline=true&page=1&page_size=50   // T0 基线
Query: ?baseline=false&page=1&page_size=50  // T1 发布后

Response 200:
{
  "code": 0,
  "data": {
    "baseline": true,
    "checked_at": "2026-07-16T10:00:00Z",
    "items": [
      {
        "engine_code": "doubao", "prompt": "静安寺皮肤管理推荐",
        "brand_mentioned": false, "rank": null, "hallucination": false,
        "citations": ["dianping.com/shop/yyy", "zhihu.com/question/zzz"]
      }
    ],
    "summary": {
      "total_prompts": 22,
      "mention_rate": 0.05,
      "avg_rank": null,
      "hallucination_rate": 0.0,
      "top_citing_domains": ["dianping.com", "zhihu.com"]
    }
  }
}
```

### GET /api/v1/user/monitor/compare

```
Query: ?t0_baseline=true&t1_baseline=false

Response 200:
{
  "code": 0,
  "data": {
    "t0": { "checked_at": "...", "mention_rate": 0.05, "hallucination_rate": 0.0 },
    "t1": { "checked_at": "...", "mention_rate": 0.15, "hallucination_rate": 0.0 },
    "delta": { "mention_rate": 0.10, "hallucination_rate": 0.0 }
  }
}
```

---

## 10. 效果舱模块（舱3）

### GET /api/v1/user/outcomes/dashboard

```
Response 200:
{
  "code": 0,
  "data": {
    "ai_kpi": {
      "mention_rate": { "t0": 0.05, "t1": 0.15, "delta": 0.10 },
      "trust_score": { "current": 0.82, "target": 0.80 },
      "citation_count": { "current": 5, "delta": 3 }
    },
    "hosted_traffic": {
      "page_views": { "this_week": 45, "delta": 12 },
      "form_submits": { "this_week": 3, "delta": 1 }
    },
    "publish_summary": {
      "total_published": 3,
      "by_channel": { "hosted": 1, "xiaohongshu": 1, "zhihu": 1 }
    },
    "funnel": {
      "exposure": { "status": "warning", "value": 0.15, "target": 0.30 },
      "trust": { "status": "ok", "value": 0.82, "target": 0.80 },
      "leads": { "status": "ok", "value": 5, "trend": "up" },
      "conversion": { "status": "pending", "value": null, "note": "等待老板录入" }
    },
    "geo_efficiency": { "score": 0.45, "formula": "(0.15达标×0.3)+(0.82达标×0.3)+(线索增长×0.2)+(待填×0.2)" },
    "iteration_draft": null
  }
}
```

---

## 11. 限流 & 错误

### 429 Too Many Requests

```
Response 429:
{ "code": 429, "data": null, "msg": "请求过于频繁，请稍后重试", "retry_after": 30 }
```

### 通用错误

```
400: { "code": 400, "data": { "field": "email", "error": "invalid" }, "msg": "参数校验失败" }
401: { "code": 401, "data": null, "msg": "登录已过期，请重新登录" }
403: { "code": 403, "data": null, "msg": "无权访问此资源" }
404: { "code": 404, "data": null, "msg": "资源不存在" }
422: { "code": 422, "data": { "detail": [...] }, "msg": "请求格式错误" }
500: { "code": 500, "data": null, "msg": "服务器内部错误" }
```

---

*API 契约 v2.1 · 对齐 10 模块 25+ 端点*
