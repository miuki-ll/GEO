# Cursor AI 强制编码规则
1. 每次生成代码前，必须完整读取 /docs/PRD.md、/docs/DESIGN.md、/docs/ARCHITECTURE.md、/docs/ROLLBACK.md
2. 严格遵循 TODO.md 任务顺序，一次只处理一个任务
3. 开发完成后对照 ROLLBACK.md 验收标准自检，不达标禁止提交commit
4. 新增功能必须同步更新对应md文档，不允许私自扩展需求范围