# GEO 数据库说明

> **版本**：v2.1 | **日期**：2026-07-16
> **关联**：[G-L2-架构设计说明书.md](G-L2-架构设计说明书.md) · [G-L1-PRD-v2.md](G-L1-PRD-v2.md)
> **ORM 路径**：`backend/app/models/`（22 张表）

---

## 0. 公共字段约定

下文不再重复列出以下字段：

| Mixin | 字段 | 说明 |
|-------|------|------|
| `TenantMixin` | `enterprise_id` | 租户 FK → `enterprises.id` · 所有业务表必含 |
| `TimestampMixin` | `created_at`, `updated_at` | 创建/更新时间 · 所有表必含 |
| 通用扩展 | `metadata_` (JSON) | 灵活扩展字段 · 按需使用 |

---

## 1. 划分逻辑（三层）

```
┌─ 第一层：租户根 ─────────────────────────────────────────┐
│  enterprises 为根；带 enterprise_id 的表都挂在其下          │
│  含：成员、门店、品牌、服务、知识库                             │
├─ 第二层：主业务链 ─────────────────────────────────────────┤
│  scenario → content_asset → publish_task → monitor_result  │
│  含：方案包、效果快照（GEO 核心流水线）                        │
├─ 第三层：支撑层 ───────────────────────────────────────────┤
│  Agent job、审计日志、全局引擎配置、向量索引运维                 │
└────────────────────────────────────────────────────────────┘
```

---

## 2. 表清单（按域分组）

### 2.1 Auth 域（租户根 · 6 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `enterprises` | 租户 | id, name, industry, industry_pack, license_no, contact_*, status, plan, settings(JSON), kb_updated_at |
| `users` | 用户 | id, enterprise_id(FK), email, password_hash, full_name, phone, role(owner/admin/editor/viewer) |
| `role_permissions` | 角色权限 | id, role, permission |
| `brands` | 品牌 | id, enterprise_id, name, logo_url, differentiator |
| `stores` | 门店 | id, enterprise_id, brand_id(FK), name, address, lat, lng, phone, hours |
| `services` | 服务项目 | id, enterprise_id, store_id(FK), name, price_range, duration, target_group, contraindications |

### 2.2 KB 域（知识库 · 4 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `kb_facts` | Fact（可发布） | id, enterprise_id, title, content, source_type, source_ref, category, tags(JSON), verified(bool) |
| `kb_faqs` | FAQ | id, enterprise_id, question, answer, source_ref, fact_refs(JSON) |
| `kb_signals` | Signal（线索） | id, enterprise_id, signal_type, content, source, confidence(int), status, expires_at |
| `kb_externals` | External（候选） | id, enterprise_id, url, raw_content, confirmed(bool→入Fact), fetched_at |

### 2.3 Strategy 域（策略 · 7 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `target_engines` | AI 平台定义（全局） | id, code, name, base_url, adapter, default_model, enabled, capabilities(JSON) |
| `source_diagnoses` | 信源诊断结果 | id, enterprise_id, engine_code, prompt, brand_mentioned(bool), rank(int), hallucination(bool), citations(JSON), competitor_mentioned(JSON) |
| `keywords` | 四层词库 | id, enterprise_id, keyword, layer(认知/选型/痛点/场景), source(RawInputs/探针反推/SEO API/LLM生成/手动), lbs_tags(JSON) |
| `scenarios` | 场景问句 | id, enterprise_id, user_query, intent, channel, skill, priority, fact_refs(JSON), target_engines(JSON) |
| `strategy_pack_drafts` | 方案包草案 | id, enterprise_id, persona(JSON), competitors(JSON), scenarios(JSON), channels(JSON), keyword_library(JSON), weights(JSON) |
| `strategy_packs` | 确认方案包 | id, enterprise_id, draft_id(FK), approved_at, approved_by(FK→users) |
| `agent_tasks` | Agent 任务 | id, enterprise_id, task_type, graph_name, celery_task_id, status, gate_status, progress_pct, progress_message, input_data(JSON), output_data(JSON), trace_id, error_message |

### 2.4 Content 域（内容 · 2 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `content_assets` | 发布内容 | id, enterprise_id, scenario_id(FK), channel, skill, title, body, fact_refs(JSON), rag_slices(JSON), status(draft/ready/published/rejected) |
| `content_drafts` | 草稿 | id, enterprise_id, content_asset_id(FK), status(draft/ready), machine_review(JSON), reviewer_id(FK) |

### 2.5 Publish 域（发布 · 1 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `publish_tasks` | 发布任务 | id, enterprise_id, content_asset_id(FK), channel, mode(AUTO/SEMI/GUIDED), status, published_url, error_message, scheduled_at, published_at |

### 2.6 Monitor 域（监测 · 3 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `monitor_profiles` | 监测配置 | id, enterprise_id, pool_type(Core/Probe), engine_codes(JSON), prompt_list(JSON), schedule |
| `monitor_results` | 监测结果 | id, enterprise_id, profile_id(FK), engine_code, prompt, brand_mentioned(bool), rank(int), hallucination(bool), citations(JSON), baseline(bool→T0/T1), checked_at |
| `outcome_snapshots` | 效果快照 | id, enterprise_id, date, mention_rate(float), trust_score(float), lead_count(int), conversion_count(int), geo_efficiency(float) |

### 2.7 Audit 域（审计 · 2 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `approval_logs` | 审批记录 | id, enterprise_id, target_type(strategy_pack+content), target_id, action(confirm/reject), user_id(FK), comment, created_at |
| `agent_traces` | Agent 审计 | id, enterprise_id, job_id, graph_name, step_idx, thought, action, action_input, observation, tokens(int), latency_ms(int) |

### 2.8 Events 域（事件 · 1 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `hosted_page_events` | 托管页埋点 | id, enterprise_id, page_url, event_type(page_view/form_submit), referer, ip, user_agent |

### 2.9 Ops 域（运维 · 1 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `faiss_indexes` | Faiss 索引 | id, enterprise_id, index_name, dimension, ntotal, last_trained_at |

---

## 3. 主业务链关系

```
enterprises (租户)
  └─ stores (门店 · NAP)
       └─ services (项目 · 价格)
  └─ kb_facts / kb_faqs / kb_signals (知识库)
  └─ source_diagnoses (诊断结果)
       └─ keywords (词库 · 从诊断反推/聚类)
            └─ scenarios (场景问句)
                 └─ strategy_pack_drafts
                      └─ strategy_packs (确认后)
                           └─ content_assets (生成内容 · fact_refs→kb_facts)
                                └─ content_drafts
                                     └─ approval_logs (人闸门)
                                          └─ publish_tasks (发布)
                                               └─ monitor_results (监测)
                                                    └─ outcome_snapshots (效果)
```

---

## 4. 关键查询路径

### 4.1 内容溯源链

```sql
-- 从发布内容追溯到 KB Fact
SELECT ca.id, ca.title, ca.fact_refs, kf.title, kf.content
FROM content_assets ca
JOIN kb_facts kf ON kf.id = ANY(ca.fact_refs)
WHERE ca.enterprise_id = :eid;

-- 从监测结果追溯到发布内容
SELECT mr.prompt, mr.brand_mentioned, pt.content_asset_id, ca.title
FROM monitor_results mr
LEFT JOIN publish_tasks pt ON pt.enterprise_id = mr.enterprise_id
LEFT JOIN content_assets ca ON ca.id = pt.content_asset_id
WHERE mr.enterprise_id = :eid
ORDER BY mr.checked_at DESC;
```

### 4.2 T0/T1 对比

```sql
-- 基线 vs 24h后 提及率对比
SELECT
  baseline.mention_rate AS t0,
  followup.mention_rate AS t1,
  (followup.mention_rate - baseline.mention_rate) AS delta
FROM outcome_snapshots baseline
JOIN outcome_snapshots followup
  ON followup.enterprise_id = baseline.enterprise_id
  AND followup.date = baseline.date + INTERVAL '1 day'
WHERE baseline.baseline = true;
```

### 4.3 租户隔离强制

```sql
-- 所有业务查询必须带 enterprise_id
-- Service 层统一注入，API 层校验跨租户 → 403

-- 举例：获取词库
SELECT * FROM keywords WHERE enterprise_id = :current_eid;
```

---

## 5. 扩展预留

| 字段/表 | 用途 | 激活版本 |
|---------|------|:--:|
| `enterprises.settings` (JSON) | 租户级配置扩展 | MVP |
| `content_assets.rag_slices` (JSON) | RAG 切片存储 | MVP |
| `keywords.source` (枚举) | 词库来源追溯 | MVP |
| `monitor_results.baseline` (bool) | T0/T1 区分 | MVP |
| `strategy_pack_drafts.weights` (JSON) | 混合权重存储 | MVP |
| IndustryPack 表（新增） | 行业包规则持久化 | V1.1 |
| `consult_logs` 表（新增） | 咨询归因 | V1.1 |

---

*数据库说明 v2.1 · 对齐 22 张表现有基线 + PRD v2.1 需求*
