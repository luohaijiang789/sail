"""ScanRun 状态机编排器。

对应 docs/08-orchestration.md。提供两种执行形态：

1. **同步进程内执行**（``run_scan_synchronous``）——本地开发与端到端验证用。
   按 DAG 拓扑序在当前进程内直接调用各阶段 worker 函数，不依赖 Celery/Redis。
   每个 worker 遵循 ``fn(scan_run_id, stage_run_id, db) -> dict`` 契约，返回
   ``{"status": "SUCCEEDED"|"FAILED"|"SKIPPED", "output": {...}, "metrics": {...}}``。
2. **回调驱动执行**（``on_stage_complete`` / ``on_stage_fail``）——生产 Celery 形态。
   Worker 通过 HTTP 回调通知，编排器推进下游。本会话先落地同步形态。

ADR-03：Celery 消息只传 scan_run_id；状态机集中在 ScanRun/ScanStageRun 上。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.domain.scan_run import (
    SCAN_RUN_FAILED,
    SCAN_RUN_PARTIAL_SUCCEEDED,
    SCAN_RUN_RUNNING,
    SCAN_RUN_SUCCEEDED,
    STAGE_DEFINITIONS,
    STAGE_DEPENDENCIES,
    STAGE_FAILED_FINAL,
    STAGE_PENDING,
    STAGE_RUNNING,
    STAGE_SKIPPED,
    STAGE_SUCCEEDED,
    ScanRun,
    ScanStageRun,
)
from app.infrastructure.database import SessionLocal

logger = get_logger("Orchestrator")

# 阶段 → worker 函数的惰性注册表。惰性导入避免循环依赖。
# 每个 worker 签名：fn(scan_run_id, stage_run_id, db) -> dict
_WORKERS: dict[str, Callable[..., dict]] = {}


def _get_worker(stage_type: str) -> Callable[..., dict]:
    if stage_type not in _WORKERS:
        _WORKERS[stage_type] = _load_worker(stage_type)
    return _WORKERS[stage_type]


def _load_worker(stage_type: str) -> Callable[..., dict]:
    """惰性加载阶段 worker 函数。返回可直接调用的函数（非 Celery task）。"""
    # ponytail: 直接复用各 worker 模块里已存在的纯函数，不绕 Celery。
    from workers import (
        ai_analyze, assemble_context, assess_security, build, enrich,
        extract, fetch, finalize, finding_candidates, merge_findings,
        persist, preflight, codeql_scan,
    )
    table = {
        "FETCH_SOURCE": fetch.fetch_source,
        "PREFLIGHT": preflight.preflight,
        "BUILD_CODEQL_DATABASE": build.build_codeql_database,
        "EXTRACT_API_FACTS": extract.extract_api_facts,
        "ENRICH_API_DEPTH": enrich.enrich_api_depth,
        "RUN_CODEQL_VULN_SCAN": codeql_scan.run_codeql_vuln_scan,
        "FINDING_CANDIDATES": finding_candidates.finding_candidates,
        "ASSEMBLE_CONTEXT": assemble_context.assemble_context,
        "AI_ANALYZE": ai_analyze.ai_analyze,
        "MERGE_FINDINGS": merge_findings.merge_findings,
        "ASSESS_API_SECURITY": assess_security.assess_api_security,
        "PERSIST_RESULTS": persist.persist_results,
        "FINALIZE": finalize.finalize,
    }
    return table[stage_type]


def run_scan_synchronous(scan_run_id: int) -> str:
    """同步执行整条扫描 DAG（进程内，不依赖 Celery/Redis）。

    按 ``STAGE_DEFINITIONS`` 的拓扑序逐阶段执行：上游全 SUCCEEDED/SKIPPED 后才跑下游；
    阶段失败时按 ``on_failure``（ABORT/DEGRADE/CONTINUE）决定中止、降级或继续。
    最终回写 ScanRun 状态并返回。

    Returns:
        ScanRun 最终状态（SUCCEEDED / PARTIAL_SUCCEEDED / FAILED）。
    """
    with SessionLocal() as db:
        scan_run = db.get(ScanRun, scan_run_id)
        if scan_run is None:
            raise ValueError(f"ScanRun {scan_run_id} not found")

        scan_run.status = SCAN_RUN_RUNNING
        scan_run.started_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("scan_started", scan_run_id=scan_run_id, mode=scan_run.mode)

        # 拓扑序遍历全部阶段
        stage_rows = db.execute(
            select(ScanStageRun)
            .where(ScanStageRun.scan_run_id == scan_run_id)
            .order_by(ScanStageRun.id)
        ).scalars().all()
        stage_by_type: dict[str, ScanStageRun] = {s.stage_type: s for s in stage_rows}

        aborted = False
        degraded = False

        for stage_type in STAGE_DEFINITIONS:  # 已是拓扑序
            stage = stage_by_type.get(stage_type)
            if stage is None:
                continue

            if aborted:
                # 已中止：剩余阶段标 SKIPPED（required）或保持 PENDING
                if stage.required:
                    stage.status = STAGE_SKIPPED
                continue

            # 1. 检查上游依赖
            deps = STAGE_DEPENDENCIES.get(stage_type, [])
            dep_states = [stage_by_type[d].status for d in deps if d in stage_by_type]
            if any(s not in (STAGE_SUCCEEDED, STAGE_SKIPPED) for s in dep_states):
                # 上游未就绪或已失败
                if stage.required:
                    stage.status = STAGE_SKIPPED
                    stage.error_message = "upstream not satisfied"
                    degraded = True
                else:
                    stage.status = STAGE_SKIPPED
                db.commit()
                continue

            # 2. 可选阶段：无对应产物输入时直接跳过（如 ENRICH 依赖深度提取，阶段一跳过）
            if not stage.required and stage_type in _OPTIONAL_SKIP_STAGES:
                stage.status = STAGE_SKIPPED
                db.commit()
                continue

            # 3. 执行 worker
            scan_run.current_stage = stage_type
            db.commit()
            logger.info("stage_dispatched", scan_run_id=scan_run_id, stage=stage_type)

            try:
                worker = _get_worker(stage_type)
                result = worker(scan_run_id, stage.id, db)
                _apply_result(db, stage, result)
            except Exception as e:  # noqa: BLE001  阶段异常统一兜底
                logger.exception("stage_exec_error", stage=stage_type, error=str(e))
                stage.status = STAGE_FAILED_FINAL
                stage.error_code = "STAGE_EXEC_ERROR"
                stage.error_message = str(e)[:1000]
                stage.finished_at = datetime.now(timezone.utc)
                stage.retryable = False
                db.commit()
                result = {"status": "FAILED"}

            # 4. 失败处理
            if stage.status in (STAGE_FAILED_FINAL,):
                on_failure = stage.on_failure
                if on_failure == "ABORT" and stage.required:
                    aborted = True
                elif on_failure == "DEGRADE":
                    degraded = True
                    logger.warning("stage_degraded", stage=stage_type)
                # CONTINUE：什么都不做，继续下游

            if stage.status == STAGE_SKIPPED and stage.required:
                degraded = True

            _update_progress(db, scan_run, stage_by_type)

        # 5. 计算 ScanRun 最终状态
        final_status = _compute_scan_run_status(stage_by_type, aborted, degraded)
        scan_run.status = final_status
        scan_run.finished_at = datetime.now(timezone.utc)
        scan_run.current_stage = None
        db.commit()

        logger.info("scan_finished", scan_run_id=scan_run_id, status=final_status)
        return final_status


# 阶段一跳过的可选阶段（深度补充、AI 分层等留到后续阶段）
_OPTIONAL_SKIP_STAGES: frozenset[str] = frozenset({
    "ENRICH_API_DEPTH",
})


def _apply_result(db: Session, stage: ScanStageRun, result: dict) -> None:
    """把 worker 返回的 dict 写回 ScanStageRun。"""
    status = (result.get("status") or "SUCCEEDED").upper()
    metrics = result.get("metrics") or result.get("output")
    stage.metrics_json = metrics
    stage.finished_at = datetime.now(timezone.utc)
    if status == "SUCCEEDED":
        stage.status = STAGE_SUCCEEDED
    elif status == "SKIPPED":
        stage.status = STAGE_SKIPPED
    else:
        stage.status = STAGE_FAILED_FINAL
        stage.error_code = result.get("error_code") or "STAGE_FAILED"
        stage.error_message = result.get("error_message") or result.get("output", {}).get("reason")
        stage.retryable = bool(result.get("retryable", False))
    db.commit()


def _update_progress(db: Session, scan_run: ScanRun, stage_by_type: dict[str, ScanStageRun]) -> None:
    done = sum(1 for s in stage_by_type.values() if s.status in (STAGE_SUCCEEDED, STAGE_SKIPPED, STAGE_FAILED_FINAL))
    total = len(stage_by_type)
    scan_run.progress = int(done / total * 100) if total else 0
    db.commit()


def _compute_scan_run_status(stage_by_type: dict[str, ScanStageRun], aborted: bool, degraded: bool) -> str:
    if aborted:
        return SCAN_RUN_FAILED
    if degraded:
        return SCAN_RUN_PARTIAL_SUCCEEDED
    return SCAN_RUN_SUCCEEDED


# === 回调驱动形态（生产 Celery）===
# 以下保留 API 形态供 HTTP 回调使用；当前同步形态已覆盖端到端流程。

def start_scan(scan_run_id: int) -> None:
    """启动扫描：置 RUNNING，派发首批可执行阶段（FETCH_SOURCE 无上游依赖）。

    生产环境由 Celery ``sail.start_scan`` task 调用。本地直接用 ``run_scan_synchronous``。
    """
    # 同步形态下直接跑完整 DAG。
    run_scan_synchronous(scan_run_id)


def on_stage_complete(stage_run_id: int, output_artifact_id: int, metrics: dict) -> None:
    """Worker 完成回调：标记 SUCCEEDED，推进下游。"""
    with SessionLocal() as db:
        stage = db.get(ScanStageRun, stage_run_id)
        if stage is None:
            return
        stage.status = STAGE_SUCCEEDED
        stage.output_artifact_id = output_artifact_id
        stage.metrics_json = metrics
        stage.finished_at = datetime.now(timezone.utc)
        db.commit()
    # 同步形态无需手动推进（已在同一调用栈完成）。
    _advance_scan(stage_run_id)


def on_stage_fail(stage_run_id: int, error_code: str, error_message: str, retryable: bool) -> None:
    """Worker 失败回调：按 retryable 走重试或 FAILED_FINAL。"""
    with SessionLocal() as db:
        stage = db.get(ScanStageRun, stage_run_id)
        if stage is None:
            return
        stage.status = STAGE_FAILED_FINAL if not retryable else STAGE_RUNNING
        stage.error_code = error_code
        stage.error_message = error_message
        stage.retryable = retryable
        stage.finished_at = datetime.now(timezone.utc) if not retryable else None
        db.commit()


def _advance_scan(scan_run_id: int) -> None:
    """回调形态下推进就绪阶段。同步形态下为空操作。"""
    return None
