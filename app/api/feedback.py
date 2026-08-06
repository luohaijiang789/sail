"""人工反馈路由（前缀 /api 在 main.py 注册）。

接收对某个 check 结果的人工反馈，驱动 Prompt/规则/模式改进闭环。
对应 docs/06-ai-analysis.md 的反馈分析流程。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

router = APIRouter()


@router.post("/api-assets/{asset_id}/checks/{check_id}/feedback")
def submit_feedback(asset_id: int, check_id: int, db: Session = Depends(get_db)) -> dict:
    """提交人工反馈。

    Body: human_verdict / human_reason / reviewer。
    会触发 FeedbackAnalysis 生成与改进建议（PROMPT/RULE/PATTERN/NO_CHANGE）。
    """
    return {}
