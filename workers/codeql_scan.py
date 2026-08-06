"""RUN_CODEQL_VULN_SCAN Worker。对应 02-build.md / 05-finding-model.md。

执行漏洞扫描产出 SARIF（或降级形态的候选数据）。CodeQL 数据库可用时跑真 CodeQL；
NO_BUILD 降级时用 Tree-sitter 污点分析器（scanner_id="sail-taint"），产出真实
source→sink 候选，统一写入 SARIF 文件供 FINDING_CANDIDATES 解析。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from scanners.codeql_runner import is_codeql_available, run_vuln_scan
from scanners.taint_analyzer import analyze_repository
from workers.celery_app import celery_app

logger = get_logger("CodeQLScanWorker")

# 阶段一默认规则包（CodeQL pack 名）
DEFAULT_RULE_PACK = "codeql/java-queries:codeql-suites/java-security-and-quality.qls"


def run_codeql_vuln_scan(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    _set_stage(db, scan_run_id, "RUN_CODEQL_VULN_SCAN", STAGE_RUNNING)

    workspace = Path(settings.workspace_root) / str(scan_run_id) / "source" / "repo"
    if not workspace.exists():
        return {"status": "FAILED", "error_code": "SOURCE_MISSING"}

    results_dir = Path(settings.workspace_root) / str(scan_run_id) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    sarif_path = results_dir / "vuln-scan.sarif"

    # 判断是否可跑真 CodeQL：DB 已构建 + CLI 可用
    codeql_db_path = Path(settings.workspace_root) / str(scan_run_id) / "codeql-db"
    use_real_codeql = (
        is_codeql_available()
        and codeql_db_path.exists()
        and (scan_run.build_quality or "").startswith("SUCCESSFUL")
    )

    if use_real_codeql:
        try:
            run_vuln_scan(str(codeql_db_path), DEFAULT_RULE_PACK, str(sarif_path))
            scanner_id = "codeql"
            logger.info("codeql_scan_done", results=str(sarif_path))
        except Exception as e:  # noqa: BLE001  CodeQL 失败回退污点分析
            logger.warning("codeql_scan_fallback_taint", error=str(e)[:300])
            _run_taint_scan(workspace, sarif_path)
            scanner_id = "sail-taint"
    else:
        # 降级：Tree-sitter 污点分析
        logger.info("taint_scan_start (no-build degraded mode)")
        _run_taint_scan(workspace, sarif_path)
        scanner_id = "sail-taint"

    result_count = _count_sarif_results(sarif_path)
    _set_stage(db, scan_run_id, "RUN_CODEQL_VULN_SCAN", STAGE_SUCCEEDED, metrics={
        "scanner_id": scanner_id, "sarif_path": str(sarif_path), "result_count": result_count,
    })
    db.commit()
    return {"status": "SUCCEEDED", "output": {
        "scanner_id": scanner_id, "sarif_path": str(sarif_path), "result_count": result_count}}


def _run_taint_scan(workspace: Path, sarif_path: Path) -> None:
    """用污点分析器扫描，结果写成 SARIF 格式（统一下游解析路径）。"""
    candidates = analyze_repository(workspace)
    sarif = _candidates_to_sarif(candidates)
    sarif_path.write_text(json.dumps(sarif, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("taint_scan_done", candidates=len(candidates))


def _candidates_to_sarif(candidates) -> dict:
    """把 FindingCandidateData 列表转成最小 SARIF 结构。"""
    results = []
    rules = {}
    for c in candidates:
        rules[c.rule_id] = {
            "id": c.rule_id,
            "name": c.rule_id,
            "defaultConfiguration": {"level": _severity_to_level(c.severity)},
            "properties": {"tags": [c.cwe] if c.cwe else [], "security-severity": c.severity},
        }
        results.append({
            "ruleId": c.rule_id,
            "level": _severity_to_level(c.severity),
            "message": {"text": f"{c.rule_id} in {c.symbol or c.file_path}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": c.file_path},
                    "region": {"startLine": c.start_line, "endLine": c.end_line},
                },
                "message": {"text": c.symbol or ""},
            }],
            "codeFlows": [{
                "threadFlows": [{
                    "locations": [
                        {"location": {"physicalLocation": {
                            "artifactLocation": {"uri": n.get("file", c.file_path)},
                            "region": {"startLine": n.get("line", 0)}},
                            "message": {"text": n.get("desc", "")}}}
                        for n in c.dataflow_path
                    ]
                }]
            }] if c.dataflow_path else [],
        })
    return {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "sail-taint", "rules": list(rules.values())}},
            "results": results,
        }],
    }


def _severity_to_level(severity: str) -> str:
    return {"CRITICAL": "error", "HIGH": "error", "MEDIUM": "warning",
            "LOW": "note", "INFO": "none"}.get(severity, "warning")


def _count_sarif_results(sarif_path: Path) -> int:
    try:
        data = json.loads(sarif_path.read_text(encoding="utf-8"))
        return sum(len(r.get("results", [])) for r in data.get("runs", []))
    except Exception:
        return 0


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


@celery_app.task(name="sail.RUN_CODEQL_VULN_SCAN")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return run_codeql_vuln_scan(scan_run_id, stage_run_id, db)
