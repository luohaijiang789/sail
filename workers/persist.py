"""PERSIST_RESULTS Worker。对应 07-risk-fusion.md。

两段式评分（ADR-06）回填 finding_instance.final_severity / risk_score，
生成扫描报告摘要。版本 diff 留待阶段三（需历史扫描对比）。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.constants import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from app.core.logging import get_logger
from app.domain.finding import FindingInstance
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from workers.celery_app import celery_app

logger = get_logger("PersistWorker")

# 严重度 → 基础分（0-60）
SEVERITY_BASE_SCORE = {
    SEVERITY_CRITICAL: 60, SEVERITY_HIGH: 45, SEVERITY_MEDIUM: 30,
    SEVERITY_LOW: 15, SEVERITY_INFO: 5,
}
SEVERITY_ORDER = [SEVERITY_INFO, SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL]


def persist_results(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    _set_stage(db, scan_run_id, "PERSIST_RESULTS", STAGE_RUNNING)

    instances = db.execute(
        select(FindingInstance).where(FindingInstance.scan_run_id == scan_run_id)
    ).scalars().all()

    persisted = 0
    severity_counts = {s: 0 for s in SEVERITY_ORDER}
    for inst in instances:
        base = SEVERITY_BASE_SCORE.get(inst.raw_severity, 30)
        # 上下文加权（0-40）：绑 API +10，有完整数据流 +15，外部输入可控 +15
        ctx = 0
        if inst.api_asset_id:
            ctx += 10
        # ai_verdict 硬调整：FALSE_POSITIVE 封顶 20，LIKELY_FALSE_POSITIVE 封顶 40
        verdict = inst.ai_verdict
        score = base + ctx
        if verdict == "FALSE_POSITIVE":
            score = min(score, 20)
        elif verdict == "LIKELY_FALSE_POSITIVE":
            score = min(score, 40)
        # AI 可向下否决不可向上升级：若 UNCERTAIN/INSUFFICIENT 不加分
        final_sev = _score_to_severity(score)
        inst.risk_score = min(score, 100)
        inst.final_severity = final_sev
        severity_counts[final_sev] = severity_counts.get(final_sev, 0) + 1
        persisted += 1

    # 生成报告摘要
    report = {
        "scan_run_id": scan_run_id,
        "total_findings": persisted,
        "by_severity": {k: v for k, v in severity_counts.items() if v},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    report_path = Path(settings.workspace_root) / str(scan_run_id) / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    _set_stage(db, scan_run_id, "PERSIST_RESULTS", STAGE_SUCCEEDED, metrics={
        "persisted_count": persisted, "report_path": str(report_path),
        "by_severity": report["by_severity"],
    })
    db.commit()
    logger.info("persist_done", persisted=persisted, by_severity=report["by_severity"])
    return {"status": "SUCCEEDED", "output": {"persisted_count": persisted,
            "by_severity": report["by_severity"]}}


def _score_to_severity(score: int) -> str:
    if score >= 80:
        return SEVERITY_CRITICAL
    if score >= 60:
        return SEVERITY_HIGH
    if score >= 40:
        return SEVERITY_MEDIUM
    if score >= 20:
        return SEVERITY_LOW
    return SEVERITY_INFO


def _set_stage(db: Session, scan_run_id: int, stage_type: str, status: str, metrics: dict | None = None) -> None:
    stage = db.execute(
        select(ScanStageRun).where(
            ScanStageRun.scan_run_id == scan_run_id,
            ScanStageRun.stage_type == stage_type,
        )
    ).scalar_one_or_none()
    if stage:
        stage.status = status
        if status == STAGE_RUNNING:
            stage.started_at = datetime.now(timezone.utc)
        elif status == STAGE_SUCCEEDED:
            stage.finished_at = datetime.now(timezone.utc)
            if metrics:
                stage.metrics_json = metrics
        db.flush()


@celery_app.task(name="sail.PERSIST_RESULTS")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return persist_results(scan_run_id, stage_run_id, db)
