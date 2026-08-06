# 10. 基础设施与部署

> [← 09-api-frontend](09-api-frontend.md)　|　下一章：[11-roadmap](11-roadmap.md)

## 项目目录结构

```
sail/
├─ app/                          # FastAPI 应用
│  ├─ main.py                    # 入口 + 路由注册 + 异常处理器注册
│  ├─ config.py                  # 配置（环境变量）
│  ├─ core/                      # 核心层（统一日志/异常/常量/结果）
│  │  ├─ logging.py              # structlog 结构化日志 + 上下文绑定
│  │  ├─ exceptions.py           # 异常体系 + 错误分类（可重试/不可重试/资源）
│  │  ├─ constants.py            # 全部常量集中（限制/退避/verdict/严重度...）
│  │  └─ result.py               # ApiResponse / StageResult / PaginatedResult
│  ├─ domain/                    # 领域模型（SQLAlchemy ORM）
│  │  ├─ source_assets.py        # Project/Repository/SourceRevision/Artifact/CodeQLDatabase
│  │  ├─ scan_run.py             # ScanRun/ScanStageRun + 阶段常量 + DAG依赖
│  │  ├─ api_asset.py            # ApiAsset/CallEdge/ResourceAccess/SecurityControl
│  │  ├─ check_and_security.py   # ApiCheck/SecurityProfile + 预定义清单 + 评分常量
│  │  └─ finding.py              # RulePack/Rule/Finding三层/AiReview/FeedbackAnalysis
│  ├─ api/                       # REST API 层
│  │  ├─ deps.py                 # 依赖注入（get_db/get_settings/require_*）
│  │  ├─ errors.py               # 全局异常处理器
│  │  ├─ pagination.py           # 分页工具
│  │  ├─ schemas/                # Pydantic DTO（与 ORM 解耦）
│  │  │  ├─ common.py            # PaginationParams/SortParams
│  │  │  ├─ repository.py        # RepositoryCreate/Update/Out
│  │  │  ├─ scan.py              # ScanCreate/Out/StageOut/EventOut
│  │  │  ├─ api_asset.py         # ApiAssetOut/CheckOut/SecurityProfileOut...
│  │  │  ├─ finding.py           # FindingOut/EvidenceOut/DataflowOut...
│  │  │  └─ feedback.py          # FeedbackCreate/Out
│  │  ├─ repositories.py         # 仓库 router
│  │  ├─ scans.py                # 扫描 router（含 SSE）
│  │  ├─ api_assets.py           # API 资产 router
│  │  ├─ findings.py             # 漏洞 router
│  │  ├─ feedback.py             # 反馈 router
│  │  └─ internal.py             # Worker 回调 router
│  ├─ application/               # 应用服务（编排逻辑）
│  │  ├─ create_scan.py          # 创建扫描 + 初始化所有阶段记录
│  │  ├─ orchestrate_scan.py     # ScanRun 状态机 + DAG 派发 + 幂等检查
│  │  └─ retry_stage.py          # 阶段重试
│  └─ infrastructure/            # 基础设施适配器（可替换）
│     ├─ interfaces.py           # Protocol 接口（Git/ObjectStorage/CodeQL/Cache/LlmProvider）
│     ├─ database.py             # SQLAlchemy engine/session
│     ├─ redis_client.py         # Redis 客户端
│     ├─ object_storage.py       # MinIO 客户端
│     ├─ git_client.py           # Git 操作封装
│     └─ codeql_cli.py           # CodeQL CLI 封装
├─ workers/                      # Celery Workers
│  ├─ celery_app.py              # Celery 实例 + 队列定义 + task_router
│  ├─ base.py                    # BaseStageWorker ABC（公共逻辑：日志/幂等/心跳/回调）
│  ├─ callbacks.py               # StageCallbackClient（Worker→API 回调）
│  ├─ fetch.py                   # FETCH_SOURCE
│  ├─ preflight.py               # PREFLIGHT
│  ├─ build.py                   # BUILD_CODEQL_DATABASE
│  ├─ extract.py                 # EXTRACT_API_FACTS
│  ├─ enrich.py                  # ENRICH_API_DEPTH
│  ├─ codeql_scan.py             # RUN_CODEQL_VULN_SCAN
│  ├─ finding_candidates.py      # FINDING_CANDIDATES
│  ├─ assemble_context.py        # ASSEMBLE_CONTEXT
│  ├─ ai_analyze.py              # AI_ANALYZE
│  ├─ merge_findings.py          # MERGE_FINDINGS
│  ├─ assess_security.py         # ASSESS_API_SECURITY
│  ├─ persist.py                 # PERSIST_RESULTS
│  └─ finalize.py                # FINALIZE
├─ extractors/                   # Tree-sitter 提取层
│  ├─ pipeline.py                # ExtractionPipeline（协调各组件统一产出）
│  ├─ java/                      # Tree-sitter Java 解析
│  │  ├─ parser.py               # parse_file/parse_source/query_nodes
│  │  ├─ source_index.py         # 源码索引
│  │  └─ symbol_table.py         # 符号表
│  ├─ frameworks/                # 框架 Adapter
│  │  ├─ base.py                 # FrameworkAdapter ABC
│  │  ├─ spring.py               # Spring MVC/WebFlux/Security
│  │  ├─ jaxrs.py                # JAX-RS
│  │  └─ servlet.py              # Servlet
│  ├─ api/                       # API 信息提取
│  │  ├─ endpoint_detector.py    # API 入口识别
│  │  ├─ param_extractor.py      # 参数提取
│  │  └─ security_scanner.py     # 安全控制扫描
│  ├─ config/                    # 配置解析
│  │  ├─ yaml_parser.py          # application.yml
│  │  ├─ properties_parser.py    # .properties
│  │  └─ mybatis_parser.py       # MyBatis Mapper XML → SQL
│  └─ models/                    # 提取层数据模型
│     ├─ endpoint.py             # ApiEndpoint
│     └─ api_asset.py            # ApiAssetData
├─ scanners/                     # CodeQL 扫描器
│  ├─ registry.py                # ScannerRegistry（可插拔扫描器注册表）
│  ├─ sdk.py                     # ScannerManifest
│  ├─ codeql_runner.py           # CodeQL 执行器
│  ├─ sarif_parser.py            # SARIF → FindingCandidateData
│  └─ postprocessors/            # 后处理器（可插拔）
│     ├─ base.py                 # BasePostprocessor ABC + 注册表
│     ├─ path_normalizer.py      # 路径标准化
│     ├─ symbol_normalizer.py    # 符号/数据流签名归一化
│     ├─ fingerprint_calculator.py  # 指纹计算（sha256）
│     ├─ deduplicator.py         # 扫描内去重
│     └─ pipeline.py             # PostprocessPipeline（串行执行）
├─ ai/                           # AI 分析层
│  ├─ schemas.py                 # EvidenceBundle/AiReviewOutput/NeedRequest
│  ├─ prompts.py                 # Guided Questions 模板 + prompt 构建
│  ├─ evidence_builder.py        # 从 API 入口构建 Evidence Bundle
│  ├─ analyzer.py                # LLM 分析 + NEED_MORE_CONTEXT 闭环
│  ├─ feedback_engine.py         # 自动优化反馈闭环
│  └─ providers/                 # LLM Provider 抽象层（可切换）
│     ├─ base.py                 # BaseLlmProvider ABC + LlmResponse
│     ├─ openai_provider.py      # OpenAI/Azure 兼容
│     ├─ anthropic_provider.py   # Anthropic Claude
│     ├─ factory.py              # Provider 工厂 + get_strong_llm/get_fast_llm
│     └─ pricing.py              # 模型价格表 + 成本计算
├─ config/                       # 外置配置
│  ├─ check_items.yaml           # 20项预定义检查清单 + 维度权重 + 评分映射
│  └─ __init__.py                # 配置加载器
├─ frontend/                     # Vue 3 前端（vue-vben-admin v5 monorepo）
│  ├─ apps/web-ele/              # Element Plus 应用
│  │  └─ src/
│  │     ├─ views/               # SAIL 业务页面
│  │     │  ├─ dashboard/        # 概览页
│  │     │  ├─ repositories/     # 仓库列表
│  │     │  ├─ scans/            # 创建扫描 + 扫描详情
│  │     │  ├─ api-assets/       # API 资产列表 + 详情
│  │     │  └─ findings/         # 漏洞列表 + 详情
│  │     ├─ api/sail/            # SAIL API 封装
│  │     ├─ router/routes/modules/  # 路由模块
│  │     └─ types/               # SAIL 前端类型
│  ├─ packages/                  # vben 核心包（布局/权限/工具）
│  ├─ internal/                  # vben 工具链（lint/tsconfig/vite-config）
│  └─ pnpm-workspace.yaml
├─ docker/                       # Docker
│  ├─ Dockerfile                 # 含 CodeQL CLI + JDK17
│  └─ docker-compose.yml         # MySQL/Redis/MinIO + Worker 容器
├─ migrations/                   # Alembic 数据库迁移
├─ tests/                        # 测试
│  ├─ unit/
│  └─ integration/
├─ scripts/setup.sh              # 开发环境初始化
├─ docs/                         # 架构文档（13份）
├─ pyproject.toml
├─ alembic.ini
├─ Makefile
├─ .env.example
├─ .editorconfig
├─ .dockerignore
├─ .gitignore
├─ LICENSE
├─ CONTRIBUTING.md
└─ README.md
```

## 分层解耦架构

```
┌─────────────────────────────────────────────────────┐
│ API 层 (app/api/)                                    │
│  router → schemas(DTO) → deps(依赖注入) → errors    │
│  不直接操作 ORM，通过 application 层                  │
├─────────────────────────────────────────────────────┤
│ Application 层 (app/application/)                    │
│  create_scan / orchestrate_scan / retry_stage        │
│  编排逻辑，不关心基础设施实现                         │
├─────────────────────────────────────────────────────┤
│ Domain 层 (app/domain/)                              │
│  ORM 模型 + 阶段常量 + DAG 依赖                       │
├─────────────────────────────────────────────────────┤
│ Infrastructure 层 (app/infrastructure/)              │
│  interfaces(Protocol) → 具体实现                     │
│  database/redis/minio/git/codeql 可替换              │
├─────────────────────────────────────────────────────┤
│ Core 层 (app/core/)                                  │
│  logging/exceptions/constants/result                 │
│  被所有层依赖                                         │
├─────────────────────────────────────────────────────┤
│ Workers (workers/)                                   │
│  base(BaseStageWorker) → 13个阶段Worker              │
│  callbacks(回调客户端)                               │
├─────────────────────────────────────────────────────┤
│ Extractors (extractors/)                             │
│  pipeline → java/frameworks/api/config/models       │
│  只依赖 Tree-sitter，不依赖 CodeQL                    │
├─────────────────────────────────────────────────────┤
│ Scanners (scanners/)                                 │
│  registry → codeql_runner → sarif_parser            │
│  postprocessors(pipeline: path→symbol→fp→dedup)     │
├─────────────────────────────────────────────────────┤
│ AI (ai/)                                             │
│  schemas/prompts/evidence_builder/analyzer           │
│  providers(base→openai/anthropic→factory)           │
│  feedback_engine                                      │
└─────────────────────────────────────────────────────┘
```

## Celery 队列

```
source_fetch / source_extract / java_build_jdk17 / codeql_query / ai_analysis / result_process / maintenance
```

## 并发估算（单机 32C/64GB）

| 队列 | 并发 | 依据 |
|---|---|---|
| source_fetch | 8 | IO密集，~500MB/任务 |
| source_extract | 4 | CPU密集，4C/任务 |
| java_build | 2 | 峰值16GB+8C/任务 |
| codeql_query | 3 | 4C+4GB/任务 |
| ai_analysis | 16 | 调LLM API，几乎不耗本地 |
| result_process | 4 | CPU+DB |

## 日志

structlog 结构化日志，每条含 `scan_run_id/stage_run_id/task_id/repository_id/commit_sha/worker`。通过 `bind_scan_context()` 绑定上下文，后续所有日志自动携带。

### 构建日志流式上传

工作区构建结束销毁，日志流式上传 MinIO：`构建输出 → tee本地 + 实时tail上传MinIO → 本地销毁 → MinIO保留`

## 可观测指标

扫描成功率、拉取失败率、构建成功率（按mode分维度）、CodeQL DB缓存命中率、平均构建时长、AI分析成功率、AI平均token/成本、单仓扫描成本、Worker排队时间。

## 构建环境隔离

```
非root用户 / 独立临时工作区 / CPU+内存+磁盘+进程数限制 / 超时
禁止访问宿主机目录 / 禁止Docker Socket / 默认禁止公司内网
只开放依赖源 / 构建结束销毁工作区
```

## Worker 权限最小化

| Worker | 有 | 无 |
|---|---|---|
| Fetch | Git凭证、MinIO写 | DB管理员、AI密钥 |
| Build | 源码读、依赖源、MinIO写 | 用户管理、AI密钥 |
| AI | LLM密钥、Evidence读 | 源码访问、DB管理员 |
| Postprocess | DB写、MinIO读 | Git凭证、AI密钥 |

## Docker Compose

```
public-network:    nginx / frontend / api
internal-network:  api / workers / mysql / redis / minio
```

MySQL/Redis/MinIO 不对公网开放。容器间用服务名访问。
