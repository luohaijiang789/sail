"""仓库管理路由（前缀 /api/repositories 在 main.py 注册）。

提供仓库的增删改查与可达性验证。仓库是扫描的入口实体，凭证按 credential_id 引用。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

router = APIRouter()


@router.post("/")
def create_repository(db: Session = Depends(get_db)) -> dict:
    """创建仓库。Body: name / git_url / default_branch / credential_id / project_id。"""
    return {}


@router.get("/")
def list_repositories(db: Session = Depends(get_db)) -> list:
    """仓库列表（支持按 project_id 过滤）。"""
    return []


@router.get("/{repository_id}")
def get_repository(repository_id: int, db: Session = Depends(get_db)) -> dict:
    """仓库详情。"""
    return {}


@router.patch("/{repository_id}")
def update_repository(repository_id: int, db: Session = Depends(get_db)) -> dict:
    """更新仓库（部分字段）。"""
    return {}


@router.post("/{repository_id}/validate")
def validate_repository(repository_id: int, db: Session = Depends(get_db)) -> dict:
    """验证仓库可达：尝试列出远端分支/commit，校验凭证有效性。"""
    return {}
