"""扫描路由（前缀 /api/scans 在 main.py 注册）。

扫描的创建、查询、取消、重试，以及阶段级重试、阶段列表、流式日志与 SSE 事件。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.pagination import paginate
from app.api.schemas.common import PaginationParams
from app.api.schemas.scan import ScanCreate, ScanOut, ScanStatsOut, StageOut
from app.application.create_scan import create_scan as create_scan_service
from app.core.exceptions import ScanRunNotFoundError
from app.core.logging import get_logger
from app.core.result import PaginatedResult
from app.domain.api_asset import ApiAsset
from app.domain.finding import Finding, FindingInstance
from app.domain.scan_run import SCAN_RUN_RUNNING, ScanRun, ScanStageRun
from app.domain.source_assets import Repository
from app.infrastructure.database import get_db

logger = get_logger(__name__)

router = APIRouter()


class ScanDetailOut(BaseModel):
    """扫描详情：ScanRun 运行态 + 全部 ScanStageRun 时间线。"""

    model_config = ConfigDict(from_attributes=True)

    scan: ScanOut
    stages: list[StageOut]


@router.post("/", response_model=ScanOut)
def create_scan(payload: ScanCreate, db: Session = Depends(get_db)) -> ScanOut:
    """创建扫描。

    Body: ``{"repository_id", "revision":{"type","value"}, "scan_profile_id", "ai_analysis"}``。
    调用 ``create_scan`` 应用服务：建 SourceRevision + ScanRun + 全量 ScanStageRun，并派发首个任务。
    """
    scan_run = create_scan_service(
        db=db,
        repository_id=payload.repository_id,
        revision=payload.revision.value,
        scan_profile_id=payload.scan_profile_id,
        ai_analysis=payload.ai_analysis,
    )
    return ScanOut.model_validate(scan_run)


@router.get("/", response_model=PaginatedResult[ScanOut])
def list_scans(
    pagination: PaginationParams = Depends(),
    repository_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResult[ScanOut]:
    """扫描列表，支持按 ``repository_id`` / ``status`` 过滤 + 分页。"""
    stmt = select(ScanRun).order_by(ScanRun.id.desc())
    if repository_id is not None:
        stmt = stmt.where(ScanRun.repository_id == repository_id)
    if status:
        stmt = stmt.where(ScanRun.status == status)

    page = paginate(db, stmt, pagination)
    return PaginatedResult[ScanOut](
        items=[ScanOut.model_validate(s) for s in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
        has_next=page.has_next,
    )


@router.get("/stats", response_model=ScanStatsOut)
def get_scan_stats(db: Session = Depends(get_db)) -> ScanStatsOut:
    """概览统计：扫描数/运行中/漏洞数/高危/仓库数/API 资产数 + 最近 5 次扫描。"""
    total_scans = db.execute(select(func.count()).select_from(ScanRun)).scalar() or 0
    running = db.execute(
        select(func.count()).select_from(ScanRun).where(ScanRun.status == SCAN_RUN_RUNNING)
    ).scalar() or 0
    succeeded = db.execute(
        select(func.count()).select_from(ScanRun).where(ScanRun.status == "SUCCEEDED")
    ).scalar() or 0
    total_findings = db.execute(select(func.count()).select_from(Finding)).scalar() or 0
    high_risk = db.execute(
        select(func.count()).select_from(FindingInstance)
        .where(FindingInstance.final_severity.in_(["HIGH", "CRITICAL"]))
    ).scalar() or 0
    total_repos = db.execute(select(func.count()).select_from(Repository)).scalar() or 0
    total_api_assets = db.execute(select(func.count()).select_from(ApiAsset)).scalar() or 0
    recent = db.execute(
        select(ScanRun).order_by(ScanRun.id.desc()).limit(5)
    ).scalars().all()
    return ScanStatsOut(
        total_scans=total_scans, running_scans=running, succeeded_scans=succeeded,
        total_findings=total_findings, high_risk_findings=high_risk,
        total_repositories=total_repos, total_api_assets=total_api_assets,
        recent_scans=[ScanOut.model_validate(s) for s in recent],
    )


@router.get("/{scan_id}", response_model=ScanDetailOut)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
) -> ScanDetailOut:
    """扫描详情：ScanRun 状态 + 全部 ScanStageRun 时间线。"""
    scan_run = db.get(ScanRun, scan_id)
    if scan_run is None:
        raise ScanRunNotFoundError(f"ScanRun {scan_id} not found")

    stage_rows = db.execute(
        select(ScanStageRun)
        .where(ScanStageRun.scan_run_id == scan_id)
        .order_by(ScanStageRun.id)
    ).scalars().all()

    return ScanDetailOut(
        scan=ScanOut.model_validate(scan_run),
        stages=[StageOut.model_validate(s) for s in stage_rows],
    )


@router.post("/{scan_id}/cancel")
def cancel_scan(
    scan_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """请求取消扫描：置 ``cancel_requested=True``，编排器在下次派发时终止。"""
    scan_run = db.get(ScanRun, scan_id)
    if scan_run is None:
        raise ScanRunNotFoundError(f"ScanRun {scan_id} not found")
    scan_run.cancel_requested = True
    db.commit()
    logger.info("scan_cancel_requested", scan_run_id=scan_run.id)
    return {"scan_id": scan_run.id, "cancel_requested": True}


@router.post("/{scan_id}/retry")
def retry_scan(scan_id: int, db: Session = Depends(get_db)) -> dict:
    """重试整个 ScanRun（重置失败阶段并重新派发）。"""
    # TODO: 调用 retry 应用服务，重置失败阶段并重新派发。
    raise NotImplementedError


@router.post("/{scan_id}/stages/{stage_id}/retry")
def retry_stage(scan_id: int, stage_id: int, db: Session = Depends(get_db)) -> dict:
    """重试指定阶段。"""
    # TODO: 调用 retry_stage 应用服务。
    raise NotImplementedError


@router.get("/{scan_id}/stages", response_model=list[StageOut])
def list_stages(
    scan_id: int,
    db: Session = Depends(get_db),
) -> list[StageOut]:
    """扫描的阶段时间线：每个 ScanStageRun 的状态/时长/指标/错误。"""
    # 校验 ScanRun 存在，不存在抛 404
    scan_run = db.get(ScanRun, scan_id)
    if scan_run is None:
        raise ScanRunNotFoundError(f"ScanRun {scan_id} not found")

    stage_rows = db.execute(
        select(ScanStageRun)
        .where(ScanStageRun.scan_run_id == scan_id)
        .order_by(ScanStageRun.id)
    ).scalars().all()
    return [StageOut.model_validate(s) for s in stage_rows]


@router.get("/{scan_id}/logs")
def get_scan_logs(scan_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    """流式日志：从 MinIO tail 构建日志并分块返回。"""
    raise NotImplementedError


@router.get("/{scan_id}/events")
def stream_scan_events(scan_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    """SSE 事件流：推送 ScanRun/ScanStageRun 状态变化，支持 Last-Event-ID 断线重连。"""
    raise NotImplementedError
