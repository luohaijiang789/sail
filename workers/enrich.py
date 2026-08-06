"""ENRICH_API_DEPTH Worker。对应 03-api-asset.md「深度层」。

阶段一跳过（编排器在 _OPTIONAL_SKIP_STAGES 中标记 SKIPPED）。此函数仅在直接调用时
执行最小实现：标记 enrichment_status，不补充 L2 字段。阶段三接入完整调用链提取。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.domain.api_asset import ApiAsset
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from workers.celery_app import celery_app

logger = get_logger("EnrichWorker")


def enrich_api_depth(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    _set_stage(db, scan_run_id, "ENRICH_API_DEPTH", STAGE_RUNNING)

    # 阶段一：只标记 enrichment_status，不补充 L2
    assets = db.execute(
        select(ApiAsset).where(ApiAsset.scan_run_id == scan_run_id)
    ).scalars().all()
    for a in assets:
        if a.enrichment_status == "INITIAL":
            a.enrichment_status = "SKIPPED_PHASE1"

    _set_stage(db, scan_run_id, "ENRICH_API_DEPTH", STAGE_SUCCEEDED, metrics={
        "enriched_count": 0, "note": "skipped in phase 1",
    })
    db.commit()
    return {"status": "SUCCEEDED", "output": {"enriched_count": 0, "note": "phase1 skip"}}


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


@celery_app.task(name="sail.ENRICH_API_DEPTH")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return enrich_api_depth(scan_run_id, stage_run_id, db)
