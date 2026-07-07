# GEO 实施清单 v4

> **版本**：V4.1 | **日期**：2026-07-04 | **关联**：PRD-v4.md · GEO-需求规格说明书.md · [`二期.md`](./二期.md)

---

## 1. 目标

MVP-A 首发 + 完整 P0 并行。**用户只见 3 步**；七段闭环见需求规格 §3。

**MVP-A 最小验收：** 主攻 engine 诊断 → 2 scenario → 托管页 + 1 渠道 SEMI → 效果舱 1 轮。

---

## 2. 三舱 vs 闭环

（同 v4.0 §2，略）

**新增验收：** thin KB 门槛（AC-18）· scenario→Core 子集（FR-MN-07）· SEMI 标准包（FR-PB-07）· AC-SEC-01

---

## 3. 阶段 0～3

同 v4.0；**变更摘要：**

| 变更 | 说明 |
|------|------|
| UX-10 | D 区 scenario 承接文案 |
| UX-11 | 方案包渐进披露 A+C / B+D 折叠 |
| UX-12 | 草稿三栏 + approval_log |
| UX-13 | onboarding 分步叙事+ ETA |
| 1.7 | SEO API → **P1**（II-06） |
| 1.9 | thin KB 硬门槛 |
| 2.5 | 诊断默认主攻 engine（FR-DG-07） |
| 3.8 | confirm 后 scenario→Core 子集 |

---

## 4. 阶段 4～7 变更

| 阶段 | 变更 |
|------|------|
| 6 发布 | FR-PB-02 **SEMI 默认**；FR-PB-07 SEMI 包；托管页 sanitize+CSP |
| 7 监测 | FR-MN-07 scenario Core 子集；MVP-A 主攻 engine 即可 |
| 安全 | FR-RB-03 rate limit；AC-SEC-01 跨 tenant 403 |
| NFR | Faiss OSS 备份；job_id 唯一键（NFR-08～09） |

---

## 5. MVP 验收（AC-01～AC-18 + AC-SEC-01）

- [ ] AC-01 **MVP-A** 路径跑通（或完整 P0）
- [ ] AC-02～AC-03 fact_refs / 禁词
- [ ] AC-04 主攻 engine Core（完整 P0：≥2 engine）
- [ ] AC-05～AC-07 隔离 / 闸门 / **SEMI 包**
- [ ] AC-08～AC-13 方案包 / scenario / 三舱
- [ ] AC-14～AC-16 Agent / 临界草案
- [ ] AC-17 content_asset_id
- [ ] **AC-18** thin KB 门槛
- [ ] **AC-SEC-01** 跨 tenant 403
- [ ] AC-11 Faiss（SEO API 非阻塞）

---

## 6. 开放 → 二期

原 §13 开放项已决策或移入 [`二期.md`](./二期.md)（II-01～II-27）。

---

## 7. 二期排期

V1.1 / V2 / V2+ 同 v4.0 §14；详 **二期.md**。

---

*实施清单 v4.1*
