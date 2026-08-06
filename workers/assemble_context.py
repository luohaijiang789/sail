"""ASSEMBLE_CONTEXT Worker。对应 06-ai-analysis.md。

从 API 入口出发为每个 FindingCandidate 构建 Evidence Bundle：入口信息 + source/sink
代码片段 + 数据流路径 + 安全控制。写入 workspace 的 evidence/{candidate_id}.json，
供 AI_ANALYZE 只读消费（D5）。无 API 关联时退化为从告警行出发。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.domain.api_asset import ApiAsset, ApiSecurityControl
from app.domain.finding import FindingCandidate
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from workers.celery_app import celery_app

logger = get_logger("AssembleContextWorker")


def assemble_context(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    _set_stage(db, scan_run_id, "ASSEMBLE_CONTEXT", STAGE_RUNNING)

    workspace = Path(settings.workspace_root) / str(scan_run_id) / "source" / "repo"
    evidence_dir = Path(settings.workspace_root) / str(scan_run_id) / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    candidates = db.execute(
        select(FindingCandidate).where(FindingCandidate.scan_run_id == scan_run_id)
    ).scalars().all()

    # 预载 API 资产 + 安全控制
    api_assets = {a.id: a for a in db.execute(
        select(ApiAsset).where(ApiAsset.scan_run_id == scan_run_id)
    ).scalars().all()}
    controls = db.execute(
        select(ApiSecurityControl).where(ApiSecurityControl.scan_run_id == scan_run_id)
    ).scalars().all()
    controls_by_api: dict[int, list] = {}
    for c in controls:
        controls_by_api.setdefault(c.api_asset_id, []).append({
            "type": c.control_type, "method": c.control_method, "value": c.control_value,
        })

    assembled = 0
    for cand in candidates:
        api = api_assets.get(cand.api_asset_id) if cand.api_asset_id else None
        bundle = _build_bundle(cand, api, controls_by_api.get(cand.api_asset_id, []), workspace)
        bundle_path = evidence_dir / f"{cand.id}.json"
        bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        # 记录 evidence_hash 到 candidate（缓存键）
        cand.evidence_bundle_id = cand.id  # 用 candidate.id 作 bundle 引用
        assembled += 1

    db.flush()
    _set_stage(db, scan_run_id, "ASSEMBLE_CONTEXT", STAGE_SUCCEEDED, metrics={
        "assembled_count": assembled, "evidence_dir": str(evidence_dir),
    })
    db.commit()
    logger.info("assemble_context_done", count=assembled)
    return {"status": "SUCCEEDED", "output": {"assembled_count": assembled}}


def _build_bundle(cand: FindingCandidate, api: ApiAsset | None, controls: list, workspace: Path) -> dict:
    """组装 Evidence Bundle。"""
    source_snippet = _read_snippet(workspace, cand.file_path,
                                   (cand.source_location or {}).get("line", cand.start_line))
    sink_snippet = _read_snippet(workspace, cand.file_path, cand.start_line)

    bundle = {
        "candidate_id": cand.id,
        "rule_id": cand.symbol,
        "severity": cand.raw_severity,
        "file_path": cand.file_path,
        "source": cand.source_location,
        "sink": cand.sink_location,
        "dataflow_path": cand.dataflow_path_json or [],
        "source_code_snippet": source_snippet,
        "sink_code_snippet": sink_snippet,
        "security_controls": controls,
    }
    if api:
        bundle["api_asset"] = {
            "http_method": api.http_method, "path": api.full_path or api.path,
            "controller": api.controller_class, "handler": api.handler_method,
            "parameters": api.parameters_json, "framework": api.framework,
        }
    bundle["evidence_hash"] = hashlib.sha256(
        json.dumps(bundle, sort_keys=True).encode()
    ).hexdigest()[:16]
    return bundle


def _read_snippet(workspace: Path, rel_path: str, line: int, ctx: int = 5) -> str:
    """读取目标行上下文代码片段。"""
    if not line:
        return ""
    fp = workspace / rel_path
    if not fp.exists():
        return ""
    try:
        lines = fp.read_text(errors="ignore").splitlines()
        start = max(0, line - 1 - ctx)
        end = min(len(lines), line + ctx)
        return "\n".join(f"{i+1}: {lines[i]}" for i in range(start, end))
    except Exception:
        return ""


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


@celery_app.task(name="sail.ASSEMBLE_CONTEXT")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return assemble_context(scan_run_id, stage_run_id, db)
