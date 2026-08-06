"""FINALIZE Worker。对应 08-orchestration.md。

扫描收尾：更新 repository.last_scanned_commit，归档报告摘要，写最终 summary。
ScanRun 终态由编排器计算，此处只做产物归档。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.domain.api_asset import ApiAsset
from app.domain.finding import FindingInstance
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from app.domain.source_assets import Repository, SourceRevision
from workers.celery_app import celery_app

logger = get_logger("FinalizeWorker")


def finalize(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    _set_stage(db, scan_run_id, "FINALIZE", STAGE_RUNNING)

    repo = db.get(Repository, scan_run.repository_id)
    source_rev = db.get(SourceRevision, scan_run.source_revision_id)

    if repo and source_rev:
        repo.last_scanned_commit = source_rev.commit_sha

    api_count = db.execute(
        select(func.count()).select_from(ApiAsset).where(ApiAsset.scan_run_id == scan_run_id)
    ).scalar() or 0
    finding_count = db.execute(
        select(func.count()).select_from(FindingInstance).where(FindingInstance.scan_run_id == scan_run_id)
    ).scalar() or 0

    summary = {
        "scan_run_id": scan_run_id,
        "repository": repo.name if repo else None,
        "commit": source_rev.commit_sha[:12] if source_rev else None,
        "build_quality": scan_run.build_quality,
        "api_asset_count": api_count,
        "finding_count": finding_count,
        "finalized_at": datetime.now(timezone.utc).isoformat(),
    }

    _set_stage(db, scan_run_id, "FINALIZE", STAGE_SUCCEEDED, metrics=summary)
    db.commit()
    logger.info("finalize_done", **summary)
    return {"status": "SUCCEEDED", "output": {"summary": summary}}


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


@celery_app.task(name="sail.FINALIZE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return finalize(scan_run_id, stage_run_id, db)
