"""仓库管理路由（前缀 /api/repositories 在 main.py 注册）。

提供仓库的增删改查与可达性验证。仓库是扫描的入口实体，凭证按 credential_id 引用。
"""

from __future__ import annotations

import subprocess

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_repository
from app.api.pagination import paginate
from app.api.schemas.common import PaginationParams
from app.api.schemas.repository import (
    RepositoryCreate,
    RepositoryOut,
    RepositoryUpdate,
    RepositoryValidateOut,
)
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.core.result import PaginatedResult
from app.domain.source_assets import Project, Repository
from app.infrastructure.database import get_db

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=RepositoryOut)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)) -> RepositoryOut:
    """创建仓库。

    入参 ``RepositoryCreate`` 携带 ``project_id``；若对应 Project 不存在则报错，
    避免悬空外键。Repository 默认状态 ACTIVE。
    """
    project = db.get(Project, payload.project_id)
    if project is None:
        raise ValidationError(f"Project {payload.project_id} not found")

    repository = Repository(
        project_id=payload.project_id,
        name=payload.name,
        git_url=payload.git_url,
        default_branch=payload.default_branch,
        credential_id=payload.credential_id,
        repository_type=payload.repository_type,
        status="ACTIVE",
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)
    logger.info(
        "repository_created",
        repository_id=repository.id,
        project_id=repository.project_id,
        name=repository.name,
    )
    return RepositoryOut.model_validate(repository)


@router.get("/", response_model=PaginatedResult[RepositoryOut])
def list_repositories(
    pagination: PaginationParams = Depends(),
    name: str | None = None,
    project_id: int | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResult[RepositoryOut]:
    """仓库列表，支持分页与 ``name`` 模糊筛选、``project_id`` 过滤。"""
    stmt = select(Repository).order_by(Repository.id.desc())
    if name:
        stmt = stmt.where(Repository.name.like(f"%{name}%"))
    if project_id is not None:
        stmt = stmt.where(Repository.project_id == project_id)

    page = paginate(db, stmt, pagination)
    return PaginatedResult[RepositoryOut](
        items=[RepositoryOut.model_validate(r) for r in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
        has_next=page.has_next,
    )


@router.get("/{repository_id}", response_model=RepositoryOut)
def get_repository(
    repository: Repository = Depends(require_repository),
) -> RepositoryOut:
    """仓库详情。``require_repository`` 依赖完成存在性校验。"""
    return RepositoryOut.model_validate(repository)


@router.patch("/{repository_id}", response_model=RepositoryOut)
def update_repository(
    payload: RepositoryUpdate,
    repository: Repository = Depends(require_repository),
    db: Session = Depends(get_db),
) -> RepositoryOut:
    """更新仓库，只更新请求体中显式提供的字段（``exclude_unset`` 语义）。"""
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(repository, field, value)
    db.commit()
    db.refresh(repository)
    logger.info("repository_updated", repository_id=repository.id, fields=list(updates.keys()))
    return RepositoryOut.model_validate(repository)


@router.post("/{repository_id}/validate", response_model=RepositoryValidateOut)
def validate_repository(
    repository: Repository = Depends(require_repository),
) -> RepositoryValidateOut:
    """验证仓库可达：用 ``git ls-remote`` 检测远端地址与默认分支是否有效。

    不克隆仓库，仅列出远端引用。超时或非零退出码视为不可达。
    """
    cmd = ["git", "ls-remote", "--heads", "--exit-code", repository.git_url]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("repository_validate_timeout", repository_id=repository.id)
        return RepositoryValidateOut(valid=False, message="git ls-remote timed out after 30s")
    except FileNotFoundError:
        logger.warning("git_not_installed", repository_id=repository.id)
        return RepositoryValidateOut(valid=False, message="git executable not found")

    if result.returncode == 0:
        return RepositoryValidateOut(valid=True, message="repository reachable")

    stderr = (result.stderr or "").strip()
    message = stderr or f"git ls-remote exited with code {result.returncode}"
    logger.info(
        "repository_validate_failed",
        repository_id=repository.id,
        returncode=result.returncode,
        stderr=stderr,
    )
    return RepositoryValidateOut(valid=False, message=message)
