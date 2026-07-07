# 如何在 Cursor 中查看 Word / PDF 资料

> 你**不需要**下载什么「文本编码器」。问题是 Cursor/VS Code **默认不能很好地预览 .docx 和 .pdf**，不是文件坏了。

---

## 推荐做法（最简单）

**工作文档统一用 Markdown（.md）**

- Cursor 原生支持，可 diff、可搜索、AI 可直接读
- 本次已把 `资料/` 下蒲公英参考 docx **提取为 .txt**，并新建了 GEO 项目的 .md 文档

| 文档 | 路径 |
|------|------|
| 老板版介绍 | `GEO-产品介绍-生美老板版.md` |
| 需求规格 | `GEO-需求规格说明书.md` |
| 概要设计 | `GEO-概要设计说明书.md` |
| 架构设计 | `GEO-架构设计说明书.md` |
| 产品 PRD | `PRD-v1.md` |
| 蒲公英参考原文 | `资料/AI蒲公英部落_-_*.txt` |

---

## 若仍想在编辑器里看 Word

在 Cursor 扩展市场搜索安装（任选）：

- **Office Viewer** / **vscode-office** — 预览 docx/xlsx
- 装完后右键 docx → Open With → 对应扩展

---

## 若仍想在编辑器里看 PDF

- 扩展：**vscode-pdf** 等
- 或在 Cursor 对话里 **@ 文件名.pdf**，AI 可读 PDF 内容（你之前 `@超前智能GEO产品.pdf` 就是这样）

---

## 批量把 docx 转成 md/txt

不需要特殊编码器。docx 本质是 zip + XML，可用：

1. **Word / WPS**：另存为 .txt 或复制到 .md  
2. **让 AI 在对话里 @ docx 文件**（部分环境支持）  
3. **命令行**（本项目已用过 PowerShell 解压 document.xml 提取文字）

---

## 建议的团队习惯

```
对外/给老板讨论  →  GEO-产品介绍-生美老板版.md
给技术评审       →  需求 + 概要 + 架构 三份 .md
内部迭代         →  PRD-v1.md
原始参考         →  资料/ 保留 docx，并保留 .txt 备份
```

**结论：不用下编码器；把日常编辑的文件改成 .md 最省事。**
