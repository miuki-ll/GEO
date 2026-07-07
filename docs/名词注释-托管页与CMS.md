# 名词注释：CMS、托管页、Schema（给非科班开发者）

> 你提到的「CMD」在本项目语境里通常指 **CMS**。下面所有术语均带注释。

---

## 一、先搞清三个概念的关系

```
客户想被 AI 看到
    ↓
需要在「网上有一个正式网页」放内容（项目介绍、FAQ 等）
    ↓
网页放哪？
    ├── 方案 A：客户自己的官网（WordPress / 易优 CMS 等）→ 我们 API 推送过去
    └── 方案 B：平台托管页（我们提供一个现成 URL）→ MVP 主推
```

| 术语 | 中文 | 一句话 |
|------|------|--------|
| **CMS** | 内容管理系统 | 发网页用的后台，像「网站的编辑器+发布按钮」 |
| **WordPress** | 开源 CMS | 全球最常见的建站后台，有 API 可对接 |
| **易优 CMS** | 国内 PHP 建站系统 | 国内小商家常用，类似 WordPress 的国产版 |
| **自建 CMS** | 自己从零做建站系统 | 工作量大，GEO 产品 MVP 不做 |
| **平台托管页** | Platform-hosted page | 平台帮客户生成网页，URL 在我们这边 |
| **Schema** | 结构化数据标记 | 网页里藏的 JSON，告诉 AI「这是店名、这是地址」 |
| **JSON-LD** | 一种写 Schema 的格式 | 放在 `<script>` 里，机器可读 |
| **LocalBusiness** | Schema 的一种类型 | 专门描述实体门店（美容店、餐厅等） |

---

## 二、平台托管页 MVP 要生成什么

一个生美门店，最少 3 类页面/块：

### 1. 门店信息页（带 LocalBusiness Schema）

**作用：** 让 AI 能准确读到「这家店是谁、在哪、怎么联系」。

| 字段 | 中文 | 必填 | 示例 |
|------|------|------|------|
| `name` | 店名 | ✅ | 悦颜皮肤管理 |
| `description` | 简介 | ✅ | 专注敏感肌护理的连锁皮肤管理中心 |
| `address` | 地址 | ✅ | 杭州市西湖区 XX 路 XX 号 |
| `telephone` | 电话 | ✅ | 0571-XXXX |
| `openingHours` | 营业时间 | ✅ | Mo-Sa 10:00-21:00 |
| `geo` | 经纬度 | 建议 | 120.xx, 30.xx |
| `url` | 网页地址 | ✅ | 平台自动分配 |
| `image` | 门店图 | 建议 | 封面图 URL |
| `priceRange` | 价格区间 | 可选 | ¥¥ |

### 2. 项目页（每个服务项目一页）

**作用：** 回答「你们做什么项目、适合谁、多少钱」。

| 字段 | 中文 | 必填 | 示例 |
|------|------|------|------|
| `projectName` | 项目名 | ✅ | 深层补水护理 |
| `summary` | 一句话概述 | ✅ | 90 分钟深层补水，改善干燥起皮 |
| `description` | 详细说明 | ✅ | 流程、步骤、使用产品（来自知识库） |
| `priceRange` | 价格区间 | ✅ | 298-498 元 |
| `suitableFor` | 适合人群 | ✅ | 干性肌、换季敏感 |
| `notSuitableFor` | 不适合 | 建议 | 急性皮炎期 |
| `duration` | 时长 | 可选 | 约 90 分钟 |
| `notes` | 注意事项 | 建议 | 护理后 24 小时避免暴晒 |
| `faqRefs` | 关联 FAQ | 可选 | 链接到下方问答 |

**生美注意：** 不写「治疗」「根治」等医疗表述。

### 3. FAQ 页（常见问题，带 FAQPage Schema）

**作用：** AI 最爱引用「问答体」内容。

| 字段 | 中文 | 必填 | 示例 |
|------|------|------|------|
| `question` | 问题 | ✅ | 敏感肌可以做补水护理吗？ |
| `answer` | 回答 | ✅ | 可以。建议先 patch 测试…（来自知识库） |
| `sourceFact` | 事实来源 | 建议 | 知识库 fact_id，防幻觉 |

MVP 建议：每店至少 **5–10 条 FAQ**，从痛点挖掘 Skill 产出。

---

## 三、Schema 长什么样（不用背，知道结构即可）

**LocalBusiness 示例（JSON-LD 格式）：**

```json
{
  "@context": "https://schema.org",
  "@type": "BeautySalon",
  "name": "悦颜皮肤管理（西湖店）",
  "description": "专注敏感肌护理",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "XX路XX号",
    "addressLocality": "杭州",
    "addressRegion": "浙江"
  },
  "telephone": "+86-571-XXXX",
  "openingHours": "Mo-Sa 10:00-21:00",
  "url": "https://geo-platform.com/s/yueyan-xihu"
}
```

**FAQPage 示例：**

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "敏感肌可以做补水护理吗？",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "可以。建议先做皮肤检测…"
    }
  }]
}
```

> **BeautySalon**：Schema.org 里表示美容院/沙龙的一种类型，比泛用的 LocalBusiness 更贴切。

---

## 四、和「发布 AUTO」的关系

| 步骤 | 谁做 | 说明 |
|------|------|------|
| 1 | Skill 生成 | 项目页 HTML/Markdown + FAQ + JSON-LD |
| 2 | 平台托管 | 写入固定 URL，对外可访问 |
| 3 | 监测 Skill | 过几周测 AI 是否引用这个 URL |

客户无 WordPress 时，**托管页就是他们的「官网 AUTO 渠道」**。

---

## 五、MVP 最小交付清单

- [ ] 1 个门店信息页 + LocalBusiness/BeautySalon Schema
- [ ] N 个项目页（知识库有几个项目几个）
- [ ] 1 个 FAQ 聚合页 + FAQPage Schema（≥5 条）
- [ ] 固定 URL，HTTPS，可被公网访问（AI 才能抓到）
- [ ] 页面带来源标注（内容来自企业知识库哪条 fact）

---

*配合 PRD-v1.md §11.3 阅读。*
