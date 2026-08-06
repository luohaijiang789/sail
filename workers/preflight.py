"""PREFLIGHT Worker。对应 02-build.md「BuildPlan」。

预检源码、识别构建工具与 JDK、生成 BuildPlan，写入 source_revision.detected_build_plan。
不执行构建（构建在 BUILD_CODEQL_DATABASE 阶段）。阶段一最小实现：识别 pom.xml/gradle。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.config import settings
from app.domain.source_assets import SourceRevision
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from workers.celery_app import celery_app

logger = get_logger("PreflightWorker")


def preflight(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    source_rev = db.get(SourceRevision, scan_run.source_revision_id)
    if not source_rev:
        return {"status": "FAILED", "error_code": "SOURCE_NOT_FOUND"}

    _set_stage_status(db, scan_run_id, "PREFLIGHT", STAGE_RUNNING)

    workspace = Path(settings.workspace_root) / str(scan_run_id) / "source" / "repo"
    if not workspace.exists():
        return {"status": "FAILED", "error_code": "SOURCE_MISSING",
                "error_message": f"source not found at {workspace}"}

    build_plan = _detect_build_plan(workspace)
    build_plan_hash = hashlib.sha256(
        json.dumps(build_plan, sort_keys=True).encode()
    ).hexdigest()

    source_rev.detected_build_plan = build_plan
    db.flush()

    _set_stage_status(db, scan_run_id, "PREFLIGHT", STAGE_SUCCEEDED, metrics={
        "build_plan": build_plan,
        "build_plan_hash": build_plan_hash,
    })
    db.commit()
    logger.info("preflight_done", build_tool=build_plan["build_tool"], jdk=build_plan["jdk_version"])
    return {"status": "SUCCEEDED", "output": {"build_plan": build_plan, "build_plan_hash": build_plan_hash}}


def _detect_build_plan(repo_root: Path) -> dict:
    """识别构建工具与 JDK。优先级：pom.xml > build.gradle > sail.yaml > 默认。"""
    pom = repo_root / "pom.xml"
    gradle = repo_root / "build.gradle"
    gradle_kts = repo_root / "build.gradle.kts"

    if pom.exists():
        build_tool = "maven"
        jdk_version = _parse_pom_java_version(pom)
    elif gradle.exists() or gradle_kts.exists():
        build_tool = "gradle"
        jdk_version = _parse_gradle_java_version(gradle if gradle.exists() else gradle_kts)
    else:
        build_tool = "unknown"
        jdk_version = "17"

    # build_mode：有明确构建工具用 MANUAL_BUILD，否则 AUTOBUILD
    build_mode = "MANUAL_BUILD" if build_tool in ("maven", "gradle") else "AUTOBUILD"
    build_command = {
        "maven": "mvn -q -DskipTests compile",
        "gradle": "./gradlew compileJava",
        "unknown": "",
    }[build_tool]

    return {
        "build_tool": build_tool,
        "build_tool_version": "3.9",
        "jdk_version": jdk_version,
        "build_command": build_command,
        "build_mode": build_mode,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def _parse_pom_java_version(pom_path: Path) -> str:
    """从 pom.xml 提取 java.version / maven.compiler.source。"""
    import re
    text = pom_path.read_text(errors="ignore")
    m = re.search(r"<java\.version>([^<]+)</java\.version>", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"<maven\.compiler\.source>([^<]+)</maven\.compiler\.source>", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"<release>([^<]+)</release>", text)
    if m:
        return m.group(1).strip()
    return "17"


def _parse_gradle_java_version(gradle_path: Path) -> str:
    import re
    text = gradle_path.read_text(errors="ignore")
    m = re.search(r"sourceCompatibility\s*=\s*['\"]?(\d+)", text)
    if m:
        return m.group(1)
    m = re.search(r"JavaLanguageVersion\.of\((\d+)\)", text)
    if m:
        return m.group(1)
    return "17"


def _set_stage_status(db: Session, scan_run_id: int, stage_type: str, status: str, metrics: dict | None = None) -> None:
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


@celery_app.task(name="sail.PREFLIGHT")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return preflight(scan_run_id, stage_run_id, db)
