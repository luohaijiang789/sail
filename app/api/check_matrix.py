"""check 矩阵全局视图路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.api_asset import ApiAsset
from app.domain.check_and_security import ApiCheck, PREDEFINED_CHECK_ITEMS
from app.infrastructure.database import get_db

router = APIRouter(prefix="/api/check-matrix", tags=["check-matrix"])


@router.get("/")
def get_check_matrix(
    scan_run_id: int = Query(..., description="扫描 ID"),
    db: Session = Depends(get_db),
) -> dict:
    """返回 API(行) × 检查项(列) 矩阵数据。"""
    apis = db.execute(
        select(ApiAsset.id, ApiAsset.full_path, ApiAsset.path, ApiAsset.controller_class)
        .where(ApiAsset.scan_run_id == scan_run_id)
        .order_by(ApiAsset.id)
    ).all()
    checks = db.execute(
        select(ApiCheck.api_asset_id, ApiCheck.check_item_key, ApiCheck.result)
        .where(ApiCheck.scan_run_id == scan_run_id)
    ).all()

    # cells[api_id][check_key] = result
    cells: dict[int, dict[str, str]] = {}
    for c in checks:
        cells.setdefault(c.api_asset_id, {})[c.check_item_key] = c.result

    return {
        "apis": [{"id": a.id, "name": a.full_path or a.path or a.controller_class} for a in apis],
        "checks": [{"key": i["key"], "name": i["name"], "category": i["category"]}
                   for i in PREDEFINED_CHECK_ITEMS],
        "cells": cells,
    }