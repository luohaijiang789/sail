# SAIL 贡献指南

## 开发环境

```bash
make dev          # 安装开发依赖
make docker-up    # 启动 MySQL/Redis/MinIO
make migrate      # 执行数据库迁移
make run-api      # 启动 API
```

## 代码规范

- Python 3.11+，类型标注完整
- `make format` 格式化，`make lint` 检查，`make typecheck` 类型检查
- 提交前必须通过 `make lint && make test`

## 分支与提交

- `main` 主分支，保持可运行
- 功能分支 `feat/xxx`，修复分支 `fix/xxx`
- Commit message 格式：`type: 描述`（feat/fix/refactor/docs/test/chore）

## 架构约束

- API 层不直接操作 ORM，通过 application 层
- Worker 不直接访问文件系统，通过 infrastructure 层
- AI 层不直接调 LLM API，通过 ai/providers 抽象层
- 提取层不依赖 CodeQL，只依赖 Tree-sitter
