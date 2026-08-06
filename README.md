# SAIL

> Java 仓库的 CodeQL + AI 漏洞扫描平台

以 API 为攻击入口起点：拉代码 → 编译 → 扫描所有 API 信息填充资产表 → CodeQL 逐项检查形成 check 表 → 动态切割上下文给 LLM 验证得 result 表 → 报告展示。

## 核心主思路：三张表 + 动态上下文组装

```
git 代码仓 → SAIL 拉取 + 编译
    ↓
① API 资产表    每个接口的各种信息，尽可能全
    ↓
② check 表      每个 API × 每个检查项 = 分级结果
                预定义必查 + CodeQL 动态发现
                PASS/LOW/MEDIUM/HIGH/CRITICAL/NOT_CHECKED
    ↓ 动态切割上下文，组装特定接口的上下文
③ result 表     LLM 从 API 入口出发验证
                引导式提问 + NEED_MORE_CONTEXT 闭环
    ↓ 报告 + 版本对比 + Vue 展示
```

## 核心设计

- **API 信息提取不用 CodeQL**——Tree-sitter 轻量提取，快速建资产表
- **CodeQL 只扫漏洞**——source-sink 发现问题
- **check 表**——每个 API × 每个检查项的分级矩阵，显式呈现覆盖度
- **从 API 入口出发验证**——Java Web 攻击入口是 API，从入口到 sink 完整链路
- **AI 漏斗验证**——CodeQL 广度 + AI 深度，剔除 >90% 误报
- **自动优化反馈闭环**——强 LLM 归因反馈，自动建议优化 prompt/规则/白名单
- **版本迭代**——API 跨版本逐项 diff + 安全分趋势

## 架构文档（12 份）

| 章 | 文档 | 内容 |
|---|---|---|
| 0 | [00-overview](docs/00-overview.md) | 目标、主思路、七条原则、总体架构 |
| 1 | [01-data-flow](docs/01-data-flow.md) | **核心数据流 + 阶段 DAG + 三张表关系 + ER 图** |
| 2 | [02-build](docs/02-build.md) | 拉代码 + 编译 + BuildPlan + CodeQL 定位 + 缓存 |
| 3 | [03-api-asset](docs/03-api-asset.md) | **API 资产表：分两层提取 + L1/L2 字段** |
| 4 | [04-check-and-security](docs/04-check-and-security.md) | **check 表 + 安全画像 + 版本对比 + 四优化** |
| 5 | [05-finding-model](docs/05-finding-model.md) | Finding 三层模型 + 指纹归一化 |
| 6 | [06-ai-analysis](docs/06-ai-analysis.md) | **从 API 出发 + 引导提问 + NEED_MORE 闭环** |
| 7 | [07-risk-fusion](docs/07-risk-fusion.md) | 后处理 + 两段式评分 |
| 8 | [08-orchestration](docs/08-orchestration.md) | 状态机 + 重试 + 幂等 |
| 9 | [09-api-frontend](docs/09-api-frontend.md) | REST API + SSE + 前端页面 |
| 10 | [10-platform](docs/10-platform.md) | 队列 + 日志 + 隔离 + 部署 |
| 11 | [11-roadmap](docs/11-roadmap.md) | 五阶段落地路线 |
| 附录 | [appendix-adr](docs/appendix-adr.md) | 24 条架构决策记录 |

## 七条设计原则

D1 固定commit / D2 CodeQL包裹编译 / D3 围绕ScanRun / D4 AI只判断 / D5 AI不实时读码 / D6 指纹不用行号 / D7 大文件进对象存储

## 代码目录

```
app/             # FastAPI + Orchestrator
workers/         # 各 Worker
extractors/      # Tree-sitter 提取
scanners/        # CodeQL
ai/              # AI 分析
migrations/      # DB 迁移
tests/           # 测试
```

## 技术栈

FastAPI · Celery · MySQL · Redis · MinIO · Vue · CodeQL CLI · Tree-sitter

## 当前状态

架构设计阶段。第一阶段启动前置见 [11-roadmap](docs/11-roadmap.md)。
