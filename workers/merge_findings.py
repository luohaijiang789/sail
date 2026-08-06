"""MERGE_FINDINGS Worker。对应 05/07-finding-model.md。

指纹归一化 + Finding upsert + FindingInstance 创建。AI 结论已由 AI_ANALYZE 产出。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.domain.finding import AiReview, Finding, FindingCandidate, FindingInstance, Rule
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from app.domain.source_assets import SourceRevision
from workers.celery_app import celery_app

logger = get_logger("MergeFindingsWorker")


def merge_findings(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        return {"status": "FAILED", "error_code": "SCAN_NOT_FOUND"}

    source_rev = db.get(SourceRevision, scan_run.source_revision_id)
    if not source_rev:
        return {"status": "FAILED", "error_code": "SOURCE_NOT_FOUND"}

    _set_stage(db, scan_run_id, "MERGE_FINDINGS", STAGE_RUNNING)

    candidates = db.execute(
        select(FindingCandidate).where(FindingCandidate.scan_run_id == scan_run_id)
    ).scalars().all()
    reviews = {r.candidate_id: r for r in db.execute(
        select(AiReview).where(
            AiReview.candidate_id.in_([c.id for c in candidates])
        )
    ).scalars().all()} if candidates else {}
    # 预载 rule_id → rule_key，供可读标题
    rule_ids = {c.rule_id for c in candidates if c.rule_id}
    rules = {r.id: r.rule_key for r in db.execute(
        select(Rule).where(Rule.id.in_(rule_ids))
    ).scalars().all()} if rule_ids else {}

    new_count = 0
    instance_ids: list[int] = []
    finding_ids: list[int] = []

    for cand in candidates:
        review = reviews.get(cand.id)
        # 指纹匹配历史 Finding（同仓库同指纹）
        finding = db.execute(
            select(Finding).where(
                Finding.repository_id == scan_run.repository_id,
                Finding.fingerprint == cand.fingerprint,
            )
        ).scalar_one_or_none()

        if finding is None:
            finding = Finding(
                repository_id=scan_run.repository_id,
                fingerprint=cand.fingerprint,
                rule_id=cand.rule_id,
                severity=cand.raw_severity,
                status="OPEN",
                first_seen_scan_id=scan_run_id,
                last_seen_scan_id=scan_run_id,
                first_seen_commit=source_rev.commit_sha,
                last_seen_commit=source_rev.commit_sha,
                api_asset_id=cand.api_asset_id,
                title=_title(cand, rules),
                description=f"{cand.symbol} in {cand.file_path}:{cand.start_line}",
            )
            db.add(finding)
            db.flush()
            finding_ids.append(finding.id)
            new_count += 1
        else:
            finding.last_seen_scan_id = scan_run_id
            finding.last_seen_commit = source_rev.commit_sha
            if finding.status == "FIXED":
                finding.status = "REAPPEARED"

        # AI verdict 影响 finding 状态
        ai_verdict = review.verdict if review else None
        if ai_verdict in ("FALSE_POSITIVE", "LIKELY_FALSE_POSITIVE"):
            finding.status = "FALSE_POSITIVE"

        instance = FindingInstance(
            finding_id=finding.id,
            scan_run_id=scan_run_id,
            source_revision_id=source_rev.id,
            candidate_id=cand.id,
            file_path=cand.file_path,
            start_line=cand.start_line,
            end_line=cand.end_line,
            symbol=cand.symbol,
            api_asset_id=cand.api_asset_id,
            raw_severity=cand.raw_severity,
            ai_verdict=ai_verdict,
            ai_confidence=review.confidence if review else None,
            status="NEW",
        )
        db.add(instance)
        db.flush()
        instance_ids.append(instance.id)

    _set_stage(db, scan_run_id, "MERGE_FINDINGS", STAGE_SUCCEEDED, metrics={
        "new_count": new_count, "instance_count": len(instance_ids),
        "finding_count": len(finding_ids),
    })
    db.commit()
    logger.info("merge_findings_done", new=new_count, instances=len(instance_ids))
    return {"status": "SUCCEEDED", "output": {"new_count": new_count,
            "instance_count": len(instance_ids)}}


def _title(cand: FindingCandidate, rules: dict[int, str]) -> str:
    rule_key = rules.get(cand.rule_id, "vulnerability")
    # 用 file_path 的文件名 + 行号做标题，避免 symbol 在 CodeQL 形态下指向不一致文件
    fname = cand.file_path.rsplit("/", 1)[-1] if cand.file_path else "unknown"
    loc = f":{cand.start_line}" if cand.start_line else ""
    return f"{rule_key} in {fname}{loc}"


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


@celery_app.task(name="sail.MERGE_FINDINGS")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return merge_findings(scan_run_id, stage_run_id, db)
