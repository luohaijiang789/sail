"""内部回调路由（前缀 /internal 在 main.py 注册）。

Worker 通过 HTTP 回调通知阶段完成/失败，编排器据此推进 DAG。
对应 docs/08-orchestration.md「Orchestrator」回调机制。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exceptions import StageNotFoundError
from app.core.logging import get_logger
from app.domain.scan_run import (
    STAGE_FAILED_FINAL,
    STAGE_FAILED_RETRYABLE,
    STAGE_SUCCEEDED,
    ScanStageRun,
)
from app.infrastructure.database import get_db

logger = get_logger(__name__)

router = APIRouter()


class StageCompleteBody(BaseModel):
    """阶段完成回调入参。"""

    output_artifact_id: int | None = Field(default=None, description="产出制品 ID")
    metrics: dict | None = Field(default=None, description="阶段指标，写入 metrics_json")


class StageFailBody(BaseModel):
    """阶段失败回调入参。"""

    error_code: str = Field(..., description="错误码，如 BUILD_TIMEOUT / LLM_RATE_LIMIT")
    error_message: str = Field(..., description="错误描述")
    retryable: bool = Field(default=False, description="是否可重试；True→FAILED_RETRYABLE，False→FAILED_FINAL")


def _get_stage_or_404(stage_id: int, db: Session) -> ScanStageRun:
    stage = db.get(ScanStageRun, stage_id)
    if stage is None:
        raise StageNotFoundError(f"ScanStageRun {stage_id} not found")
    return stage


@router.post("/stages/{stage_id}/complete")
def stage_complete(
    stage_id: int,
    body: StageCompleteBody,
    db: Session = Depends(get_db),
) -> dict:
    """阶段完成回调。

    Body: ``output_artifact_id`` / ``metrics``。
    标记阶段 SUCCEEDED，记录产出制品与指标，更新 finished_at。
    下游推进由 ``orchestrate_scan.on_stage_complete`` 负责（待编排器实现后接入）。
    """
    stage = _get_stage_or_404(stage_id, db)
    stage.status = STAGE_SUCCEEDED
    stage.output_artifact_id = body.output_artifact_id
    if body.metrics is not None:
        stage.metrics_json = body.metrics
    stage.finished_at = datetime.utcnow()
    db.commit()

    logger.info(
        "stage_completed",
        stage_run_id=stage.id,
        scan_run_id=stage.scan_run_id,
        output_artifact_id=stage.output_artifact_id,
    )
    return {
        "stage_id": stage.id,
        "scan_run_id": stage.scan_run_id,
        "status": stage.status,
    }


@router.post("/stages/{stage_id}/fail")
def stage_fail(
    stage_id: int,
    body: StageFailBody,
    db: Session = Depends(get_db),
) -> dict:
    """阶段失败回调。

    Body: ``error_code`` / ``error_message`` / ``retryable``。
    ``retryable=True`` → ``FAILED_RETRYABLE``；``retryable=False`` → ``FAILED_FINAL``。
    记录错误码/错误信息/retryable/finished_at。下游重试或中止由编排器按 on_failure 决定。
    """
    stage = _get_stage_or_404(stage_id, db)
    stage.status = STAGE_FAILED_RETRYABLE if body.retryable else STAGE_FAILED_FINAL
    stage.error_code = body.error_code
    stage.error_message = body.error_message
    stage.retryable = body.retryable
    stage.finished_at = datetime.utcnow()
    db.commit()

    logger.info(
        "stage_failed",
        stage_run_id=stage.id,
        scan_run_id=stage.scan_run_id,
        status=stage.status,
        error_code=stage.error_code,
    )
    return {
        "stage_id": stage.id,
        "scan_run_id": stage.scan_run_id,
        "status": stage.status,
        "retryable": stage.retryable,
    }
