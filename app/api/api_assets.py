"""API 资产路由（前缀 /api/api-assets 在 main.py 注册）。

按 API 资产维度组织：详情、调用链树、资源访问、安全控制、check 矩阵、漏洞、版本历史。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

router = APIRouter()


@router.get("/")
def list_api_assets(db: Session = Depends(get_db)) -> list:
    """API 资产列表（支持按 scan_run_id / repository_id / method / path 过滤）。"""
    return []


@router.get("/{asset_id}")
def get_api_asset(asset_id: int, db: Session = Depends(get_db)) -> dict:
    """API 资产详情：入口信息 + L1/L2 字段。"""
    return {}


@router.get("/{asset_id}/call-tree")
def get_call_tree(asset_id: int, db: Session = Depends(get_db)) -> dict:
    """调用链树：ApiCallEdge 按父子关系组装成树。"""
    return {}


@router.get("/{asset_id}/resources")
def get_resources(asset_id: int, db: Session = Depends(get_db)) -> list:
    """资源访问列表：DB/SQL/HTTP 出站等 ApiResourceAccess。"""
    return []


@router.get("/{asset_id}/security")
def get_security(asset_id: int, db: Session = Depends(get_db)) -> dict:
    """安全画像：ApiSecurityProfile + ApiSecurityControl。"""
    return {}


@router.get("/{asset_id}/checks")
def get_checks(asset_id: int, db: Session = Depends(get_db)) -> list:
    """check 矩阵：每个 ApiCheck 检查项的分级结果。"""
    return []


@router.get("/{asset_id}/findings")
def get_asset_findings(asset_id: int, db: Session = Depends(get_db)) -> list:
    """该 API 的漏洞清单（finding_candidate / finding_instance）。"""
    return []


@router.get("/{asset_id}/history")
def get_asset_history(asset_id: int, db: Session = Depends(get_db)) -> list:
    """版本历史：该 API 在历次扫描中的安全分/状态变化。"""
    return []
