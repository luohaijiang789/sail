"""FINDING_CANDIDATES Worker。对应 05-finding-model.md。

解析 SARIF → finding_candidate 记录（含指纹 D6/ADR-09，不用行号），关联到 API 资产。
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.domain.api_asset import ApiAsset
from app.domain.finding import FindingCandidate, Rule, RulePack
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from app.domain.source_assets import SourceRevision
from scanners.sarif_parser import parse_sarif
from workers.celery_app import celery_app

logger = get_logger("FindingCandidatesWorker")


def finding_candidates(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    source_rev = db.get(SourceRevision, scan_run.source_revision_id)
    if not source_rev:
        return {"status": "FAILED", "error_code": "SOURCE_NOT_FOUND"}

    _set_stage(db, scan_run_id, "FINDING_CANDIDATES", STAGE_RUNNING)

    sarif_path = Path(settings.workspace_root) / str(scan_run_id) / "results" / "vuln-scan.sarif"
    if not sarif_path.exists():
        _set_stage(db, scan_run_id, "FINDING_CANDIDATES", STAGE_SUCCEEDED, metrics={"candidate_count": 0})
        db.commit()
        return {"status": "SUCCEEDED", "output": {"candidate_count": 0}}

    candidates_data = parse_sarif(str(sarif_path))

    # 从 SARIF tool driver 名取 scanner_id（sail-taint / CodeQL）
    scanner_id = "codeql"
    try:
        import json
        sarif_json = json.loads(sarif_path.read_text(encoding="utf-8"))
        for run in sarif_json.get("runs", []):
            tool_name = run.get("tool", {}).get("driver", {}).get("name", "")
            if tool_name:
                scanner_id = tool_name.lower()
                break
    except Exception:
        pass

    # 规一化 rule_id：CodeQL 形如 "java/sql-injection"，统一去 "java/" 前缀成 "sql-injection"
    # 便于与 check 表 RULE_TO_CHECK、Rule.rule_key 对齐
    for cd in candidates_data:
        if cd.rule_id and cd.rule_id.startswith("java/"):
            cd.rule_id = cd.rule_id[len("java/"):]

    # 确保有默认 RulePack + Rule 记录
    rule_map = _ensure_rules(db, candidates_data)

    # 加载本扫描的 API 资产，按 file_path 索引（用于关联 api_asset_id）
    api_assets = db.execute(
        select(ApiAsset).where(ApiAsset.scan_run_id == scan_run_id)
    ).scalars().all()
    assets_by_file: dict[str, list[ApiAsset]] = {}
    for a in api_assets:
        assets_by_file.setdefault(a.file_path, []).append(a)

    created = 0
    for cd in candidates_data:
        # 关联 API 资产：同文件优先，否则 None
        api_asset_id = None
        same_file = assets_by_file.get(cd.file_path, [])
        if same_file:
            api_asset_id = same_file[0].id

        # 指纹：rule_id + file_path + 归一化 source/sink 符号，不用行号（D6）
        # 含 file_path 避免不同文件的同类漏洞被过度归并
        fp_src = cd.source_location.get("symbol", "") if cd.source_location else ""
        fp_sink = cd.sink_location.get("symbol", "") if cd.sink_location else ""
        fingerprint = hashlib.sha256(
            f"{cd.rule_id}:{cd.file_path}:{cd.symbol}:{fp_src}:{fp_sink}".encode()
        ).hexdigest()[:16]

        rule_id = rule_map.get(cd.rule_id)
        candidate = FindingCandidate(
            scan_run_id=scan_run_id,
            scanner_id=scanner_id,
            scanner_version="1.0",
            rule_id=rule_id,
            raw_severity=cd.severity,
            raw_confidence=0.7,
            file_path=cd.file_path,
            start_line=cd.start_line,
            end_line=cd.end_line,
            symbol=cd.symbol,
            source_location=cd.source_location or None,
            sink_location=cd.sink_location or None,
            dataflow_path_json=cd.dataflow_path or None,
            api_asset_id=api_asset_id,
            fingerprint=fingerprint,
            status="NEW",
        )
        db.add(candidate)
        created += 1

    db.flush()
    _set_stage(db, scan_run_id, "FINDING_CANDIDATES", STAGE_SUCCEEDED, metrics={
        "candidate_count": created, "sarif_path": str(sarif_path),
    })
    db.commit()
    logger.info("finding_candidates_done", count=created)
    return {"status": "SUCCEEDED", "output": {"candidate_count": created}}


def _ensure_rules(db: Session, candidates_data) -> dict[str, int]:
    """为出现的 rule_id 创建 Rule 记录（若缺），返回 rule_id→rule.id 映射。"""
    rule_pack = db.execute(select(RulePack).where(RulePack.name == "sail-default")).scalar_one_or_none()
    if not rule_pack:
        rule_pack = RulePack(name="sail-default", version="1.0",
                             codeql_pack_name="codeql/java-queries", status="ACTIVE")
        db.add(rule_pack)
        db.flush()

    rule_map: dict[str, int] = {}
    seen = {cd.rule_id for cd in candidates_data}
    for rid in seen:
        rule = db.execute(select(Rule).where(Rule.rule_key == rid)).scalar_one_or_none()
        if not rule:
            rule = Rule(
                rule_pack_id=rule_pack.id,
                rule_key=rid,
                name=rid,
                category="DATAFLOW",
                cwe=None,
                default_severity="HIGH",
                requires_dataflow=True,
                description=f"{rid} detected by SAIL taint analysis",
                enabled=True,
            )
            db.add(rule)
            db.flush()
        rule_map[rid] = rule.id
    return rule_map


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


@celery_app.task(name="sail.FINDING_CANDIDATES")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return finding_candidates(scan_run_id, stage_run_id, db)
