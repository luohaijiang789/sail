"""FastAPI 依赖注入。

集中暴露路由可注入的依赖：DB session、配置、对象存储与 Redis 单例，
以及把路径参数校验为 ORM 对象的 ``require_*`` 依赖。

复用既有单例，避免在路由层重复构造客户端：
- ``get_db`` 直接来自 ``app.infrastructure.database``
- ``get_object_storage`` 返回 ``object_storage.minio_client``
- ``get_redis`` 返回 ``redis_client.redis_client``
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.core.exceptions import (
    ApiAssetNotFoundError,
    FindingNotFoundError,
    RepositoryNotFoundError,
    ScanRunNotFoundError,
)
from app.domain.api_asset import ApiAsset
from app.domain.finding import Finding
from app.domain.scan_run import ScanRun
from app.domain.source_assets import Repository
from app.infrastructure.database import get_db
from app.infrastructure.object_storage import minio_client
from app.infrastructure.redis_client import redis_client


def get_settings() -> Settings:
    """返回全局 ``settings`` 单例。"""
    return settings


def get_object_storage() -> type(minio_client):
    """返回 MinIO 客户端单例。"""
    return minio_client


def get_redis() -> type(redis_client):
    """返回 Redis 客户端单例。"""
    return redis_client


def require_scan_run(scan_run_id: int, db: Session = Depends(get_db)) -> ScanRun:
    """路径参数 ``scan_run_id`` → ``ScanRun``，不存在抛 404。"""
    scan_run = db.get(ScanRun, scan_run_id)
    if scan_run is None:
        raise ScanRunNotFoundError(f"ScanRun {scan_run_id} not found")
    return scan_run


def require_api_asset(asset_id: int, db: Session = Depends(get_db)) -> ApiAsset:
    """路径参数 ``asset_id`` → ``ApiAsset``，不存在抛 404。"""
    api_asset = db.get(ApiAsset, asset_id)
    if api_asset is None:
        raise ApiAssetNotFoundError(f"ApiAsset {asset_id} not found")
    return api_asset


def require_finding(finding_id: int, db: Session = Depends(get_db)) -> Finding:
    """路径参数 ``finding_id`` → ``Finding``，不存在抛 404。"""
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise FindingNotFoundError(f"Finding {finding_id} not found")
    return finding


def require_repository(repository_id: int, db: Session = Depends(get_db)) -> Repository:
    """路径参数 ``repository_id`` → ``Repository``，不存在抛 404。"""
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise RepositoryNotFoundError(f"Repository {repository_id} not found")
    return repository
