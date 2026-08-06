# 12. 实现状态与运行指南

> [← 11-roadmap](11-roadmap.md)　|　[附录：ADR](appendix-adr.md)

记录阶段一最小闭环的**已实现**内容、降级路径、以及如何运行验证。
本文档随实现推进更新，与架构设计文档（00–11）互补：前者讲"怎么设计"，本文讲"做了什么、怎么跑"。

## 已实现：完整 13 阶段 DAG 端到端跑通

`FETCH → PREFLIGHT → BUILD → EXTRACT → (ENRICH) → CODEQL_SCAN → FINDING_CANDIDATES → ASSEMBLE_CONTEXT → AI_ANALYZE → MERGE_FINDINGS → ASSESS_API_SECURITY → PERSIST → FINALIZE` 全部 13 个阶段已实现并在 WebGoat 上端到端验证通过。

### 编排器（同步形态）

`app/application/orchestrate_scan.py` 的 `run_scan_synchronous(scan_run_id)`：

- 按 `STAGE_DEFINITIONS` 拓扑序在**进程内**直接调用各阶段 worker 函数，不依赖 Celery/Redis。
- 每阶段 worker 契约：`fn(scan_run_id, stage_run_id, db) -> dict`，返回 `{status, output, metrics}`。
- 上游全 SUCCEEDED/SKIPPED 才派发下游；阶段失败按 `on_failure`（ABORT/DEGRADE/CONTINUE）处理。
- `create_scan` 在 Celery 不可用时回退到**后台线程**跑 `run_scan_synchronous`，使 REST API `POST /api/scans/` 能真实触发扫描并轮询状态。
- 生产 Celery 形态（回调驱动）的 `on_stage_complete` / `on_stage_fail` 保留 API 形态，阶段二接线。

### 13 个阶段实现要点

| 阶段 | 实现 |
|---|---|
| FETCH_SOURCE | git clone（浅克隆/指定 commit），建 SourceRevision + source_fingerprint |
| PREFLIGHT | 识别 pom.xml/build.gradle → build_plan（build_tool/jdk_version/build_mode），写 detected_build_plan |
| BUILD_CODEQL_DATABASE | CodeQL 可用则 `codeql database create`；不可用或构建失败 → DEGRADE 为 NO_BUILD，下游继续 |
| EXTRACT_API_FACTS | Tree-sitter 提取 Spring/JAX-RS/Servlet handler → ApiAsset + ApiSecurityControl（按方法绑定） |
| ENRICH_API_DEPTH | 阶段一 SKIPPED（编排器跳过），只标记 enrichment_status |
| RUN_CODEQL_VULN_SCAN | CodeQL DB 可用跑真 CodeQL；否则内置 Tree-sitter 污点分析（scanner_id=sail-taint），统一输出 SARIF |
| FINDING_CANDIDATES | 解析 SARIF → finding_candidate（指纹不用行号 D6，关联 api_asset_id） |
| ASSEMBLE_CONTEXT | 从 API 入口出发为每个候选构建 Evidence Bundle（source/sink 代码片段+数据流+控制），写 workspace JSON |
| AI_ANALYZE | 配 LLM key 调真 LLM（providers 抽象层）；否则规则启发式兜底（model_name=sail-heuristic-v1），产出结构化 AiReview |
| MERGE_FINDINGS | 指纹历史匹配 → Finding upsert + FindingInstance；AI verdict 影响 finding 状态 |
| ASSESS_API_SECURITY | 每个 API × 20 检查项 = check 表（候选按 rule_key 落到对应检查项）+ 四维度安全画像 |
| PERSIST_RESULTS | 两段式评分（ADR-06）回填 final_severity/risk_score；AI 向下否决不向上升级；生成 report.json |
| FINALIZE | 更新 repository.last_scanned_commit，归档 summary |

### 降级路径（明确标注，非真实 CodeQL/LLM 时仍产出真实结果）

| 组件 | 真实路径 | 降级路径（当前 WebGoat 验证用） | 区分标记 |
|---|---|---|---|
| 漏洞扫描 | CodeQL CLI + DB | Tree-sitter 污点分析（过程内 source→sink） | `scanner_id` = `codeql` / `sail-taint` |
| AI 验证 | OpenAI/Anthropic LLM | 规则启发式（数据流完整性+严重度+绑 API） | `model_name` = LLM 名 / `sail-heuristic-v1` |

降级原因：WebGoat 要求 Java 25（环境为 21，mvn 编译失败）+ CodeQL CLI 未就绪 + 未配 LLM key。
装好 CodeQL CLI（设 `SAIL_CODEQL_CLI_PATH`）并用 Java 25 构建后，BUILD 与 SCAN 自动切真 CodeQL；
配 `SAIL_LLM_API_KEY` 后 AI_ANALYZE 自动切真 LLM。无需改代码。

## WebGoat 验证结果

```
扫描完成：ScanRun #1  状态=SUCCEEDED  进度=100%  build_quality=NO_BUILD_DEGRADED
  ① API 资产表：198 个 API（Tree-sitter 提取）
  ② check 表：3960 条检查结果（198 API × 20 检查项）+ 198 个安全画像
  ③ result 表：5 个漏洞实例
```

5 个真实漏洞（均为已知 WebGoat 故意漏洞，AI 启发式判定 LIKELY_TRUE_POSITIVE）：

| 严重度 | 规则 | 位置 |
|---|---|---|
| MEDIUM | sql-injection | jwt/claimmisuse/JWTHeaderKIDEndpoint.java:73（JWT kid header 拼 SQL） |
| MEDIUM | sql-injection | pathtraversal/ProfileUpload.java:43 |
| MEDIUM | sql-injection | pathtraversal/ProfileUploadFix.java:43 |
| MEDIUM | sql-injection | pathtraversal/ProfileUploadRemoveUserInput.java:41 |
| MEDIUM | path-traversal | webwolf/FileServer.java:79 |

> 严重度为 MEDIUM 是两段式评分结果（HIGH 基础分 + 上下文加权，但启发式 confidence 0.65 未达 HIGH 阈值）。
> 配真 LLM 后 verdict/confidence 更精确，严重度会更贴近真实可利用性。

## 如何运行

### 前置

- Python 3.11+（venv 已装依赖：fastapi/celery/tree-sitter/sqlalchemy 等）
- git、Java（CodeQL 真实路径需 Java 25 编译 WebGoat；降级路径不需要编译）
- 可选：CodeQL CLI（设 `SAIL_CODEQL_CLI_PATH`）、LLM API key（设 `SAIL_LLM_API_KEY`）

### 一键端到端（脚本，同步形态）

```bash
# 默认对本地 /tmp/webgoat 克隆执行完整 DAG
.venv/bin/python scripts/run_scan.py

# 指定远程仓库
.venv/bin/python scripts/run_scan.py --git-url https://github.com/WebGoat/WebGoat.git --branch main --name WebGoat
```

脚本完成：建表 → 注册 Project/Repository → create_scan → run_scan_synchronous → 打印三张表摘要。

### API 驱动（FastAPI 服务）

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
# 1. 注册仓库
curl -X POST localhost:8000/api/repositories/ -H 'Content-Type: application/json' -d \
  '{"name":"WebGoat","git_url":"https://github.com/WebGoat/WebGoat.git","default_branch":"main","project_id":1}'

# 2. 创建扫描（自动后台线程执行全 DAG）
curl -X POST localhost:8000/api/scans/ -H 'Content-Type: application/json' -d \
  '{"repository_id":1,"revision":{"type":"branch","value":"main"},"ai_analysis":true}'

# 3. 轮询状态
curl localhost:8000/api/scans/1

# 4. 取结果
curl 'localhost:8000/api/api-assets/?scan_run_id=1&page_size=5'   # ① API 资产表
curl 'localhost:8000/api/api-assets/95/checks'                     # ② check 表
curl 'localhost:8000/api/api-assets/95/security'                   # ② 安全画像
curl 'localhost:8000/api/findings/?repository_id=1'                # ③ result 表
curl localhost:8000/api/findings/1                                 # 漏洞详情
```

> 列表端点用尾斜杠（`/api/findings/`），无斜杠会 307 重定向。

### 数据库

本地默认 SQLite（`./sail.db`），首次运行自动 `create_all` 建表。生产用 MySQL（`SAIL_MYSQL_URL` + Alembic 迁移）。

## 前端

`frontend/` 为 vue-vben-admin v5 模板，阶段一未定制对接。结果通过上述 REST API 暴露，前端可按 [09-api-frontend](09-api-frontend.md) 接入。

## 阶段一已跳过（留待后续阶段）

- ENRICH_API_DEPTH 深度调用链（阶段三）
- 增量扫描 / 版本 diff（阶段三，需历史扫描对比）
- AI 分层过滤 / 反馈闭环（阶段四）
- 真实 Celery/Redis/MinIO 部署形态（当前同步形态已覆盖功能验证）
- 前端定制
