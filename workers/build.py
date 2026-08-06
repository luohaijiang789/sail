"""BUILD_CODEQL_DATABASE Worker。对应 02-build.md。

阶段一最小实现：尝试 CodeQL database create（maven 编译）；失败或 CodeQL 不可用时
降级为 NO_BUILD（on_failure=DEGRADE）。降级后下游 EXTRACT（Tree-sitter，不需编译）
与污点分析扫描仍可进行；真 CodeQL 扫描跳过。
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.constants import (
    BUILD_QUALITY_NO_BUILD,
    BUILD_QUALITY_SUCCESSFUL_AUTOBUILD,
)
from app.core.logging import get_logger
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED, STAGE_FAILED_FINAL
from app.domain.source_assets import CodeQLDatabase, SourceRevision
from scanners.codeql_runner import create_database, is_codeql_available
from workers.celery_app import celery_app

logger = get_logger("BuildWorker")


def build_codeql_database(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    source_rev = db.get(SourceRevision, scan_run.source_revision_id)
    if not source_rev:
        return {"status": "FAILED", "error_code": "SOURCE_NOT_FOUND"}

    _set_stage(db, scan_run_id, "BUILD_CODEQL_DATABASE", STAGE_RUNNING)

    workspace = Path(settings.workspace_root) / str(scan_run_id) / "source" / "repo"
    if not workspace.exists():
        return {"status": "FAILED", "error_code": "SOURCE_MISSING"}

    build_plan = source_rev.detected_build_plan or {}
    build_command = build_plan.get("build_command") or None
    build_plan_hash = hashlib.sha256(str(build_plan).encode()).hexdigest()[:16]

    db_dir = Path(settings.workspace_root) / str(scan_run_id) / "codeql-db"
    db_path = str(db_dir)

    # CodeQL 不可用 → NO_BUILD 降级（DEGRADE 语义，返回 SUCCEEDED）
    if not is_codeql_available():
        logger.warning("codeql_unavailable_degrade")
        scan_run.build_quality = BUILD_QUALITY_NO_BUILD
        _set_stage(db, scan_run_id, "BUILD_CODEQL_DATABASE", STAGE_SUCCEEDED, metrics={
            "build_quality": BUILD_QUALITY_NO_BUILD, "codeql_db_path": None, "degraded": True,
        })
        db.commit()
        return {"status": "SUCCEEDED", "output": {"build_quality": BUILD_QUALITY_NO_BUILD,
                                                    "codeql_db_path": None, "degraded": True}}

    # 尝试构建 CodeQL DB
    try:
        create_database(str(workspace), db_path, build_command=build_command)
        codeql_db = CodeQLDatabase(
            source_revision_id=source_rev.id,
            build_plan_hash=build_plan_hash,
            codeql_version="2.22.4",
            language="java-kotlin",
            build_mode=build_plan.get("build_mode", "MANUAL_BUILD"),
            quality=BUILD_QUALITY_SUCCESSFUL_AUTOBUILD,
            cache_key=f"{source_rev.commit_sha}:{build_plan_hash}",
            status="READY",
            source_file_count=sum(1 for _ in workspace.rglob("*.java")),
        )
        db.add(codeql_db)
        db.flush()
        scan_run.build_quality = BUILD_QUALITY_SUCCESSFUL_AUTOBUILD
        _set_stage(db, scan_run_id, "BUILD_CODEQL_DATABASE", STAGE_SUCCEEDED, metrics={
            "build_quality": BUILD_QUALITY_SUCCESSFUL_AUTOBUILD,
            "codeql_db_path": db_path, "codeql_database_id": codeql_db.id,
        })
        db.commit()
        return {"status": "SUCCEEDED", "output": {
            "build_quality": BUILD_QUALITY_SUCCESSFUL_AUTOBUILD,
            "codeql_db_path": db_path, "codeql_database_id": codeql_db.id}}
    except Exception as e:  # noqa: BLE001  构建失败降级
        logger.warning("build_failed_degrade", error=str(e)[:300])
        scan_run.build_quality = BUILD_QUALITY_NO_BUILD
        _set_stage(db, scan_run_id, "BUILD_CODEQL_DATABASE", STAGE_SUCCEEDED, metrics={
            "build_quality": BUILD_QUALITY_NO_BUILD, "degraded": True,
            "build_error": str(e)[:300], "codeql_db_path": None,
        })
        db.commit()
        return {"status": "SUCCEEDED", "output": {"build_quality": BUILD_QUALITY_NO_BUILD,
                                                    "degraded": True, "codeql_db_path": None}}


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
        elif status in (STAGE_SUCCEEDED, STAGE_FAILED_FINAL):
            stage.finished_at = datetime.now(timezone.utc)
            if metrics:
                stage.metrics_json = metrics
        db.flush()


@celery_app.task(name="sail.BUILD_CODEQL_DATABASE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return build_codeql_database(scan_run_id, stage_run_id, db)
