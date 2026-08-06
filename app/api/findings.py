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
    db: Session = Depends(get_db),
) -> PaginatedResult[FindingListOut]:
    """漏洞列表，支持按 ``severity`` / ``status`` / ``repository_id`` 过滤 + 分页。"""
    stmt = select(Finding).order_by(Finding.id.desc())
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if status:
        stmt = stmt.where(Finding.status == status)
    if repository_id is not None:
        stmt = stmt.where(Finding.repository_id == repository_id)

    page = paginate(db, stmt, pagination)
    return PaginatedResult[FindingListOut](
        items=[FindingListOut.model_validate(f) for f in page.items],
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
    """证据包：SARIF 片段、源码上下文、AI Review 响应等。"""
    # TODO: 聚合 FindingCandidate.evidence_bundle / AiReview.response_json。
    return {}


@router.get("/{finding_id}/dataflow")
def get_finding_dataflow(finding_id: int, db: Session = Depends(get_db)) -> dict:
    """数据流可视化：Source → CallPath → Sink 的路径节点。"""
    # TODO: 从 FindingCandidate.dataflow_path_json 组装 DataflowOut。
    return {}
