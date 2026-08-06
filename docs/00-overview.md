# 00. 概览与总体架构

> [← README](../README.md)　|　下一章：[01-data-flow](01-data-flow.md)

## 解决什么问题

对一个 Java 仓库的固定版本，以 API 为攻击入口起点：拉代码 → 编译 → 扫描所有 API 信息填充资产表 → CodeQL 逐项检查形成 check 表 → 动态切割上下文给 LLM 验证得 result 表 → 报告展示 + 版本对比。

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

Java Web 的攻击入口绝大部分是 API。每个检查项先定位到所属 API，从 API 入口方法开始构建完整调用链上下文（入口→sink 每一跳），让 AI 做人类审计式逻辑验证。

## 七条设计原则

| 编号 | 原则 |
|---|---|
| D1 | 固定 commit——扫描钉到 commit_sha，不接受"分支" |
| D2 | CodeQL 包裹编译——禁止重复编译 |
| D3 | 围绕 ScanRun 设计——Celery 消息只传 scan_run_id |
| D4 | AI 只判断不发现——不自由扫描仓库 |
| D5 | AI 不实时读代码——只读 Evidence Bundle（可 NEED_MORE_CONTEXT 闭环补取） |
| D6 | 指纹不用行号——基于符号和数据流签名 |
| D7 | 大文件进对象存储——MySQL 只存结构化数据 |

## 总体架构

```mermaid
flowchart TB
    U[用户/CI] --> FE[Vue 前端]
    FE --> API[FastAPI]
    API --> DB[(MySQL)]
    API --> R[(Redis)]
    API --> OBJ[(MinIO)]
    API --> ORCH[Scan Orchestrator]
    subgraph Workers[Worker 池，同一代码库不同队列]
        direction LR
        FETCH[Fetch] BUILD[Build] EXTRACT[Extract] QUERY[CodeQL] AI[AI] POST[Postprocess]
    end
    ORCH --> R --> Workers
    FETCH --> REPO[Git] & OBJ
    BUILD --> OBJ
    AI --> LLM[LLM API]
```

## 技术选型

| 组件 | 选型 |
|---|---|
| Web | FastAPI |
| 任务 | Celery |
| 业务库 | MySQL |
| 队列/缓存 | Redis |
| 对象存储 | MinIO |
| 前端 | Vue 3 + vue-vben-admin v5 + Element Plus |
| CodeQL | CodeQL CLI（只扫漏洞，不提取 API 信息） |
| API 提取 | Tree-sitter + 框架 Adapter（轻量） |
| LLM | OpenAI / Anthropic（通过 providers 抽象层可切换） |
| 日志 | structlog 结构化日志 |

## 分层解耦架构

```
API 层        router → schemas(DTO) → deps → errors     不直接操作 ORM
Application   create_scan / orchestrate_scan             编排逻辑
Domain        ORM 模型 + 阶段常量 + DAG 依赖
Infrastructure interfaces(Protocol) → 具体实现            可替换
Core          logging / exceptions / constants / result  被所有层依赖
Workers       base(BaseStageWorker) → 13个阶段Worker
Extractors    pipeline → java/frameworks/api/config     只依赖 Tree-sitter
Scanners      registry → codeql_runner → postprocessors 可插拔
AI            schemas/prompts/evidence → providers       LLM 可切换
```

## 部署形态

第一阶段 Docker Compose，模块化单体代码库 + 多 Worker 容器 + Vue 前端。不微服务化。

```
sail/                # 一个代码库
├─ app/              # FastAPI + Core + Domain + API + Application + Infrastructure
├─ workers/          # Celery + 13 个阶段 Worker
├─ extractors/       # Tree-sitter 提取层
├─ scanners/         # CodeQL 扫描器 + 后处理器
├─ ai/               # AI 分析 + LLM providers
├─ config/           # 外置配置（检查项 YAML）
├─ frontend/         # Vue 3 前端（vue-vben-admin）
├─ docker/           # Dockerfile + docker-compose
├─ migrations/       # Alembic 迁移
└─ tests/            # 测试
```

## 不做的事（第一阶段）

多 Agent、自动修复、跨仓分析、复杂权限、Istio、增量扫描、CI/CD 阻断。见 [11-roadmap](11-roadmap.md)。
