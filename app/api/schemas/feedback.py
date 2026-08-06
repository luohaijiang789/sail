"""人工反馈相关 DTO。

对应 ``app.domain.finding.FeedbackAnalysis``。
``FeedbackCreate`` 为提交入参，``FeedbackOut`` 为分析后产出（含改进类型与根因）。
"""

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    """提交人工反馈入参。"""

    human_verdict: str = Field(..., max_length=30, description="人工判定，如 TRUE_POSITIVE/FALSE_POSITIVE")
    human_reason: str = Field(..., description="人工理由，自由文本")
    reviewer: str | None = Field(default=None, max_length=100, description="评审人标识")


class FeedbackOut(BaseModel):
    """反馈分析结果输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    improvement_type: str | None = Field(
        default=None, description="改进类型：PROMPT/RULE/PATTERN/NO_CHANGE"
    )
    suggestion_status: str = Field(
        default="PENDING", description="建议状态：PENDING/APPROVED/REJECTED/APPLIED"
    )
    root_cause: str | None = Field(default=None, description="根因分析")
