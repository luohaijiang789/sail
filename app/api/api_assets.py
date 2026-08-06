"""API 资产路由（前缀 /api/api-assets 在 main.py 注册）。

按 API 资产维度组织：详情、调用链树、资源访问、安全控制、check 矩阵、漏洞、版本历史。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_api_asset
from app.api.pagination import paginate
from app.api.schemas.api_asset import (
    ApiAssetListOut,
    ApiAssetOut,
    CallEdgeOut,
    CheckOut,
    ResourceAccessOut,
    SecurityControlOut,
    SecurityProfileOut,
)
from app.api.schemas.common import PaginationParams
from app.api.schemas.finding import FindingListOut
from app.core.result import PaginatedResult
from app.domain.api_asset import (
    ApiAsset,
    ApiCallEdge,
    ApiResourceAccess,
    ApiSecurityControl,
)
from app.domain.check_and_security import ApiCheck, ApiSecurityProfile
from app.domain.finding import Finding
from app.infrastructure.database import get_db

router = APIRouter()


@router.get("/", response_model=PaginatedResult[ApiAssetListOut])
def list_api_assets(
    pagination: PaginationParams = Depends(),
    scan_run_id: int | None = None,
    repository_id: int | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResult[ApiAssetListOut]:
    """API 资产列表，支持按 ``scan_run_id`` / ``repository_id`` 过滤 + 分页。

    列表精简版额外补 ``overall_score``（来自 ApiSecurityProfile）与 ``finding_count``
    （关联 Finding 数），用批量查询避免逐行 N+1。
    """
    stmt = select(ApiAsset).order_by(ApiAsset.id.desc())
    if scan_run_id is not None:
        stmt = stmt.where(ApiAsset.scan_run_id == scan_run_id)
    if repository_id is not None:
        stmt = stmt.where(ApiAsset.repository_id == repository_id)

    page = paginate(db, stmt, pagination)
    asset_ids = [a.id for a in page.items]

    scores: dict[int, int] = {}
    finding_counts: dict[int, int] = {}
    if asset_ids:
        score_rows = db.execute(
            select(ApiSecurityProfile.api_asset_id, ApiSecurityProfile.overall_score)
            .where(ApiSecurityProfile.api_asset_id.in_(asset_ids))
        ).all()
        scores = {row[0]: row[1] for row in score_rows}

        count_rows = db.execute(
            select(Finding.api_asset_id, func.count(Finding.id))
            .where(Finding.api_asset_id.in_(asset_ids))
            .group_by(Finding.api_asset_id)
        ).all()
        finding_counts = {row[0]: row[1] for row in count_rows}

    items = [
        ApiAssetListOut(
            id=a.id,
            http_method=a.http_method,
            path=a.path,
            controller_class=a.controller_class,
            overall_score=scores.get(a.id),
            finding_count=finding_counts.get(a.id, 0),
            status=a.status,
        )
        for a in page.items
    ]
    return PaginatedResult[ApiAssetListOut](
        items=items,
        total=page.total,
        page=page.page,
        page_size=page.page_size,
        has_next=page.has_next,
    )


@router.get("/{asset_id}", response_model=ApiAssetOut)
def get_api_asset(
    asset: ApiAsset = Depends(require_api_asset),
) -> ApiAssetOut:
    """API 资产详情：L1 入口信息 + L2 深度字段。``require_api_asset`` 完成存在性校验。"""
    return ApiAssetOut.model_validate(asset)


@router.get("/{asset_id}/call-tree", response_model=list[CallEdgeOut])
def get_call_tree(
    asset: ApiAsset = Depends(require_api_asset),
    db: Session = Depends(get_db),
) -> list[CallEdgeOut]:
    """调用链边：查 ``api_call_edge WHERE api_asset_id``，按 depth/parent 组装。

    返回扁平边列表（CallEdgeOut），前端可按 ``parent_edge_id`` 自行组树；
    此处按 depth, id 排序保证拓扑序。
    """
    rows = db.execute(
        select(ApiCallEdge)
        .where(ApiCallEdge.api_asset_id == asset.id)
        .order_by(ApiCallEdge.depth, ApiCallEdge.id)
    ).scalars().all()
    return [
        CallEdgeOut(
            depth=r.depth,
            caller=r.caller_symbol,
            callee=r.callee_symbol,
            file=r.caller_file,
            line=r.caller_line,
            edge_kind=r.edge_kind,
        )
        for r in rows
    ]


@router.get("/{asset_id}/resources", response_model=list[ResourceAccessOut])
def get_resources(
    asset: ApiAsset = Depends(require_api_asset),
    db: Session = Depends(get_db),
) -> list[ResourceAccessOut]:
    """资源访问列表：查 ``api_resource_access WHERE api_asset_id``。"""
    rows = db.execute(
        select(ApiResourceAccess)
        .where(ApiResourceAccess.api_asset_id == asset.id)
        .order_by(ApiResourceAccess.id)
    ).scalars().all()
    return [
        ResourceAccessOut(
            resource_type=r.resource_type,
            resource_name=r.resource_name,
            operation=r.operation,
            is_sensitive=r.is_sensitive,
        )
        for r in rows
    ]


@router.get("/{asset_id}/security")
def get_security(
    asset: ApiAsset = Depends(require_api_asset),
    db: Session = Depends(get_db),
) -> dict:
    """安全画像：ApiSecurityProfile（若有）+ ApiSecurityControl 列表。"""
    profile = db.execute(
        select(ApiSecurityProfile)
        .where(ApiSecurityProfile.api_asset_id == asset.id)
        .order_by(ApiSecurityProfile.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    control_rows = db.execute(
        select(ApiSecurityControl)
        .where(ApiSecurityControl.api_asset_id == asset.id)
        .order_by(ApiSecurityControl.id)
    ).scalars().all()

    return {
        "profile": SecurityProfileOut.model_validate(profile) if profile else None,
        "controls": [SecurityControlOut.model_validate(c) for c in control_rows],
    }


@router.get("/{asset_id}/checks", response_model=list[CheckOut])
def get_checks(
    asset: ApiAsset = Depends(require_api_asset),
    db: Session = Depends(get_db),
) -> list[CheckOut]:
    """check 矩阵：查 ``api_check WHERE api_asset_id``。"""
    rows = db.execute(
        select(ApiCheck)
        .where(ApiCheck.api_asset_id == asset.id)
        .order_by(ApiCheck.id)
    ).scalars().all()
    return [
        CheckOut(
            check_item_key=r.check_item_key,
            check_item_name=r.check_item_name,
            result=r.result,
            evidence_summary=r.evidence_summary,
        )
        for r in rows
    ]


@router.get("/{asset_id}/findings", response_model=list[FindingListOut])
def get_asset_findings(
    asset: ApiAsset = Depends(require_api_asset),
    db: Session = Depends(get_db),
) -> list[FindingListOut]:
    """该 API 的漏洞清单：查 ``finding WHERE api_asset_id``。"""
    rows = db.execute(
        select(Finding)
        .where(Finding.api_asset_id == asset.id)
        .order_by(Finding.id.desc())
    ).scalars().all()
    return [FindingListOut.model_validate(f) for f in rows]


@router.get("/{asset_id}/history")
def get_asset_history(asset_id: int, db: Session = Depends(get_db)) -> list:
    """版本历史：该 API 在历次扫描中的安全分/状态变化。"""
    # TODO: 跨扫描聚合 ApiSecurityProfile 历史，需要 api_asset 版本追踪表。
    return []
