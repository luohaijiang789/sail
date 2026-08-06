"""内部回调路由（前缀 /internal 在 main.py 注册）。

Worker 通过 HTTP 回调通知阶段完成/失败，编排器据此推进 DAG。
对应 docs/08-orchestration.md「Orchestrator」回调机制。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

router = APIRouter()


@router.post("/stages/{stage_id}/complete")
def stage_complete(stage_id: int, db: Session = Depends(get_db)) -> dict:
    """阶段完成回调。

    Body: output_artifact_id / metrics。
    调用 orchestrate_scan.on_stage_complete 推进下游。
    """
    return {}


@router.post("/stages/{stage_id}/fail")
def stage_fail(stage_id: int, db: Session = Depends(get_db)) -> dict:
    """阶段失败回调。

    Body: error_code / error_message / retryable。
    调用 orchestrate_scan.on_stage_fail 走重试或终止。
    """
    return {}
