"""扫描路由（前缀 /api/scans 在 main.py 注册）。

扫描的创建、查询、取消、重试，以及阶段级重试、阶段列表、流式日志与 SSE 事件。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

router = APIRouter()


@router.post("/")
def create_scan(db: Session = Depends(get_db)) -> dict:
    """创建扫描。

    Body: ``{"repository_id", "revision":{"type","value"}, "scan_profile_id", "ai_analysis"}``。
    """
    return {}


@router.get("/")
def list_scans(db: Session = Depends(get_db)) -> list:
    """扫描列表（支持按 repository_id / status 过滤）。"""
    return []


@router.get("/{scan_id}")
def get_scan(scan_id: int, db: Session = Depends(get_db)) -> dict:
    """扫描详情：状态、当前阶段、进度、构建质量、失败原因。"""
    return {}


@router.post("/{scan_id}/cancel")
def cancel_scan(scan_id: int, db: Session = Depends(get_db)) -> dict:
    """请求取消扫描：置 cancel_requested=True，编排器在下次派发时终止。"""
    return {}


@router.post("/{scan_id}/retry")
def retry_scan(scan_id: int, db: Session = Depends(get_db)) -> dict:
    """重试整个 ScanRun（重置失败阶段并重新派发）。"""
    return {}


@router.post("/{scan_id}/stages/{stage_id}/retry")
def retry_stage(scan_id: int, stage_id: int, db: Session = Depends(get_db)) -> dict:
    """重试指定阶段。"""
    return {}


@router.get("/{scan_id}/stages")
def list_stages(scan_id: int, db: Session = Depends(get_db)) -> list:
    """扫描的阶段时间线：每个 ScanStageRun 的状态/时长/指标/错误。"""
    return []


@router.get("/{scan_id}/logs")
def get_scan_logs(scan_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    """流式日志：从 MinIO tail 构建日志并分块返回。"""
    raise NotImplementedError


@router.get("/{scan_id}/events")
def stream_scan_events(scan_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    """SSE 事件流：推送 ScanRun/ScanStageRun 状态变化，支持 Last-Event-ID 断线重连。"""
    raise NotImplementedError
