# 08. 编排、状态机与重试

> [← 07-risk-fusion](07-risk-fusion.md)　|　下一章：[09-api-frontend](09-api-frontend.md)

## ScanRun 状态机（ADR-03）

围绕 ScanRun 设计，不围绕 Celery Task。Celery 消息只传 `scan_run_id`。

状态：`CREATED / QUEUED / RUNNING / SUCCEEDED / PARTIAL_SUCCEEDED / FAILED / CANCELLED`

| 当前 | 事件 | 目标 | 条件 |
|---|---|---|---|
| CREATED | 提交 Celery | QUEUED | |
| QUEUED | 拾取 | RUNNING | |
| RUNNING | 所有 required 阶段成功，无降级 | SUCCEEDED | |
| RUNNING | 所有 required 阶段成功，有 DEGRADE | PARTIAL_SUCCEEDED | 如 NO_BUILD 降级 |
| RUNNING | 任一 required+ABORT 阶段 FAILED_FINAL | FAILED | |
| RUNNING | cancel_requested | CANCELLED | |

**PARTIAL_SUCCEEDED**：所有 required 阶段成功，但发生了 DEGRADE 降级或非必需阶段 SKIPPED。

## ScanStageRun

```
scan_stage_run: id, scan_run_id, stage_type, status, attempt, max_attempts,
  required(bool), on_failure(ABORT/DEGRADE/CONTINUE), celery_task_id,
  input_fingerprint, output_artifact_id, started_at, finished_at, heartbeat_at,
  retryable, error_code, error_message, metrics_json
```

阶段状态：PENDING / RUNNING / SUCCEEDED / FAILED_RETRYABLE / FAILED_FINAL / SKIPPED / CANCELLED / TIMEOUT

## 阶段依赖关系

```
FETCH_SOURCE → PREFLIGHT → BUILD_CODEQL_DATABASE
                    ├─→ EXTRACT_API_FACTS → ENRICH_API_DEPTH
                    └─→ RUN_CODEQL_VULN_SCAN → FINDING_CANDIDATES

EXTRACT_API_FACTS + ENRICH_API_DEPTH + FINDING_CANDIDATES → ASSEMBLE_CONTEXT → AI_ANALYZE
AI_ANALYZE + FINDING_CANDIDATES + API资产 → MERGE_FINDINGS → ASSESS_API_SECURITY → PERSIST_RESULTS → FINALIZE
```

EXTRACT_API_FACTS 不等 ENRICH_API_DEPTH——资产表初版立即可用。

## 阶段 required/on_failure

| 阶段 | required | on_failure |
|---|---|---|
| FETCH_SOURCE / PREFLIGHT | ✓ | ABORT |
| BUILD_CODEQL_DATABASE | ✓ | DEGRADE（降级NO_BUILD） |
| EXTRACT_API_FACTS | ✓* | ABORT |
| ENRICH_API_DEPTH | ✗ | CONTINUE |
| RUN_CODEQL_VULN_SCAN / FINDING_CANDIDATES | ✓ | ABORT |
| ASSEMBLE_CONTEXT / AI_ANALYZE | ✗ | CONTINUE |
| MERGE_FINDINGS / PERSIST_RESULTS / FINALIZE | ✓ | ABORT |
| ASSESS_API_SECURITY | ✗ | CONTINUE |

\* BUILD 降级 NO_BUILD 时 SKIPPED。

## 幂等检查（派发前）

Orchestrator 派发前检查：`status==SUCCEEDED 且 input_fingerprint 匹配 → 标 SKIPPED，推进下游`。

## 错误分类

| 类别 | 示例 | 处理 |
|---|---|---|
| 可重试 | 网络错误/存储错误/LLM限流/DB短暂故障/Worker崩溃 | 指数退避重试 |
| 不可重试 | 仓库不存在/认证失败/构建脚本错误/JDK不兼容/QL语法错误 | FAILED_FINAL |
| 资源 | OOM/DISK/CPU_TIMEOUT/BUILD_TIMEOUT | 提升资源重试，超限后降级或失败 |

### 资源错误决策

```
attempt < max_attempts？
  是 → 提升配额重试（OOM×1.5上限24GB / DISK×2 / TIMEOUT×1.5）
  否 → 看 on_failure：ABORT→FAILED_FINAL / DEGRADE→降级 / CONTINUE→SKIPPED
```

资源错误重试上限：默认 2 次（共 3 次执行）。

### 退避

```
attempt 1 失败 → 等 30s
attempt 2 失败 → 等 120s
attempt 3 失败 → FAILED_FINAL
```

LLM 限流特殊：用 Retry-After header。

## Orchestrator

API 进程内的编排逻辑，不Worker。按 DAG 拓扑序派发：上游全 SUCCEEDED 后派发下游。Worker 通过 API 回调通知完成/失败。
