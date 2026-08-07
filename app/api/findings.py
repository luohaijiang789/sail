"""漏洞路由（前缀 /api/findings 在 main.py 注册）。

漏洞列表、详情、状态变更、证据包与数据流可视化。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_finding
from app.api.pagination import paginate
from app.api.schemas.common import PaginationParams
from app.api.schemas.finding import (
    FindingListOut,
    FindingOut,
    FindingStatusUpdate,
)
from app.core.logging import get_logger
from app.core.result import PaginatedResult
from app.domain.finding import Finding
from app.infrastructure.database import get_db

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=PaginatedResult[FindingListOut])
def list_findings(
    pagination: PaginationParams = Depends(),
    severity: str | None = None,
    status: str | None = None,
    repository_id: int | None = None,
    keyword: str | None = None,
    statuses: str | None = None,
    rule_ids: str | None = None,
    cwes: str | None = None,
    ai_verdicts: str | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResult[FindingListOut]:
    """漏洞列表，支持 keyword 模糊 + 多选(逗号分隔) + repository_id 过滤 + 分页。"""
    from app.domain.api_asset import ApiAsset
    from app.domain.finding import FindingInstance, Rule

    stmt = select(Finding).order_by(Finding.id.desc())
    if severity:
        # severity 支持单值与逗号分隔多值
        stmt = stmt.where(Finding.severity.in_(severity.split(",")))
    if status:
        stmt = stmt.where(Finding.status == status)
    if statuses:
        stmt = stmt.where(Finding.status.in_(statuses.split(",")))
    if repository_id is not None:
        stmt = stmt.where(Finding.repository_id == repository_id)
    if rule_ids:
        stmt = stmt.where(Finding.rule_id.in_(
            [int(x) for x in rule_ids.split(",") if x.isdigit()]))
    if cwes:
        stmt = stmt.where(Finding.rule_id.in_(
            select(Rule.id).where(Rule.cwe.in_(cwes.split(",")))))
    if keyword:
        # ponytail: Finding 无 file_path 列，keyword 只匹配 title
        stmt = stmt.where(Finding.title.like(f"%{keyword}%"))
    # ponytail: ai_verdicts 过滤需 join FindingInstance，阶段一暂不实现

    page = paginate(db, stmt, pagination)
    # 预载关联：Rule → rule_key/cwe，ApiAsset → api_path
    rule_ids_in_page = [f.rule_id for f in page.items if f.rule_id]
    rule_map = {r.id: r for r in db.execute(
        select(Rule).where(Rule.id.in_(rule_ids_in_page))
    ).scalars().all()} if rule_ids_in_page else {}
    asset_ids = [f.api_asset_id for f in page.items if f.api_asset_id]
    assets = {a.id: a for a in db.execute(
        select(ApiAsset).where(ApiAsset.id.in_(asset_ids))
    ).scalars().all()} if asset_ids else {}
    # 批量取最近 instance 的 ai_verdict（denormalized on FindingInstance）
    finding_ids = [f.id for f in page.items]
    ai_verdicts_map: dict[int, str | None] = {}
    if finding_ids:
        for fid, verdict in db.execute(
            select(FindingInstance.finding_id, FindingInstance.ai_verdict)
            .where(FindingInstance.finding_id.in_(finding_ids))
            .order_by(FindingInstance.finding_id, FindingInstance.id.desc())
        ).all():
            if fid not in ai_verdicts_map:  # first occurrence = latest
                ai_verdicts_map[fid] = verdict
    items = []
    for f in page.items:
        out = FindingListOut.model_validate(f)
        rule = rule_map.get(f.rule_id)
        if rule:
            out.rule_key = rule.rule_key
            out.cwe = rule.cwe
        if f.api_asset_id and f.api_asset_id in assets:
            out.api_path = assets[f.api_asset_id].full_path or assets[f.api_asset_id].path
        out.ai_verdict = ai_verdicts_map.get(f.id)
        items.append(out)
    return PaginatedResult[FindingListOut](
        items=items,
        total=page.total,
        page=page.page,
        page_size=page.page_size,
        has_next=page.has_next,
    )


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(
    finding: Finding = Depends(require_finding),
) -> FindingOut:
    """漏洞详情：基本信息 + 关联 api_asset_id。``require_finding`` 完成存在性校验。"""
    return FindingOut.model_validate(finding)


@router.patch("/{finding_id}/status", response_model=FindingOut)
def update_finding_status(
    payload: FindingStatusUpdate,
    finding: Finding = Depends(require_finding),
    db: Session = Depends(get_db),
) -> FindingOut:
    """变更漏洞状态（OPEN/FIXED/REAPPEARED/FALSE_POSITIVE）。"""
    finding.status = payload.status
    db.commit()
    db.refresh(finding)
    logger.info("finding_status_updated", finding_id=finding.id, status=finding.status)
    return FindingOut.model_validate(finding)


@router.get("/{finding_id}/evidence")
def get_finding_evidence(finding_id: int, db: Session = Depends(get_db)) -> dict:
    """证据包：AI Review 结构化输出 + 候选 source/sink/dataflow。"""
    from app.domain.finding import AiReview, FindingCandidate, FindingInstance
    inst = db.execute(
        select(FindingInstance).where(FindingInstance.finding_id == finding_id)
        .order_by(FindingInstance.id.desc())
    ).scalars().first()
    if not inst or not inst.candidate_id:
        return {"ai_review": None, "candidate": None}
    cand = db.get(FindingCandidate, inst.candidate_id)
    review = db.get(AiReview, cand.ai_review_id) if cand and cand.ai_review_id else None
    return {
        "ai_review": review.response_json if review else None,
        "verdict": review.verdict if review else None,
        "confidence": review.confidence if review else None,
        "candidate": {
            "rule_id": cand.rule_id, "raw_severity": cand.raw_severity,
            "file_path": cand.file_path, "start_line": cand.start_line,
            "symbol": cand.symbol, "source_location": cand.source_location,
            "sink_location": cand.sink_location,
            "dataflow_path": cand.dataflow_path_json,
        } if cand else None,
    }


@router.get("/{finding_id}/dataflow")
def get_finding_dataflow(finding_id: int, db: Session = Depends(get_db)) -> dict:
    """数据流可视化：Source → CallPath → Sink 的路径节点。"""
    from app.domain.finding import FindingCandidate, FindingInstance
    inst = db.execute(
        select(FindingInstance).where(FindingInstance.finding_id == finding_id)
        .order_by(FindingInstance.id.desc())
    ).scalars().first()
    if not inst or not inst.candidate_id:
        return {"nodes": [], "source": None, "sink": None}
    cand = db.get(FindingCandidate, inst.candidate_id)
    if not cand:
        return {"nodes": [], "source": None, "sink": None}
    return {
        "source": cand.source_location,
        "sink": cand.sink_location,
        "nodes": cand.dataflow_path_json or [],
    }
