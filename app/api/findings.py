"""漏洞路由（前缀 /api/findings 在 main.py 注册）。

漏洞列表、详情、状态变更、证据包与数据流可视化。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

router = APIRouter()


@router.get("/")
def list_findings(db: Session = Depends(get_db)) -> list:
    """漏洞列表（按 severity / rule / cwe / ai_verdict / api_asset_id / status 过滤）。"""
    return []


@router.get("/{finding_id}")
def get_finding(finding_id: int, db: Session = Depends(get_db)) -> dict:
    """漏洞详情：基本信息 + AI 结论 + 修复建议。"""
    return {}


@router.patch("/{finding_id}/status")
def update_finding_status(finding_id: int, db: Session = Depends(get_db)) -> dict:
    """变更漏洞状态（OPEN/FIXED/FALSE_POSITIVE 等）。"""
    return {}


@router.get("/{finding_id}/evidence")
def get_finding_evidence(finding_id: int, db: Session = Depends(get_db)) -> dict:
    """证据包：SARIF 片段、源码上下文、AI Review 响应等。"""
    return {}


@router.get("/{finding_id}/dataflow")
def get_finding_dataflow(finding_id: int, db: Session = Depends(get_db)) -> dict:
    """数据流可视化：Source → CallPath → Sink 的路径节点。"""
    return {}
