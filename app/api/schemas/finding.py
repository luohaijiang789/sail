"""漏洞相关 DTO。

对应 ``app.domain.finding`` 模型（Finding / FindingInstance / FindingCandidate /
AiReview）。输出 DTO 设 ``from_attributes=True`` 以从 ORM 实例转换。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FindingOut(BaseModel):
    """漏洞完整输出。对应 ``Finding`` 表字段，含关联 ``api_asset_id``。

    列表端点已 join 出的展示字段（rule_key/cwe/api_path/file_path/ai_verdict）
    在详情端点同样填充，前端详情页直接复用，避免二次请求。
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    api_asset_id: int | None = Field(default=None, description="关联 API 资产 ID")
    fingerprint: str
    rule_id: int | None
    severity: str = Field(..., description="INFO/LOW/MEDIUM/HIGH/CRITICAL")
    status: str = Field(..., description="OPEN/FIXED/REAPPEARED/FALSE_POSITIVE")
    first_seen_scan_id: int | None
    last_seen_scan_id: int | None
    first_seen_commit: str | None
    last_seen_commit: str | None
    title: str
    description: str | None
    remediation: str | None
    created_at: datetime
    # 关联展示字段（详情端点 join 填充，详见 app/api/findings.py:get_finding）
    rule_key: str | None = None
    cwe: str | None = None
    file_path: str | None = None
    api_path: str | None = None
    ai_verdict: str | None = None


class FindingInstanceOut(BaseModel):
    """漏洞实例输出。对应 ``FindingInstance``：某次扫描中的具体定位与 AI 结论。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    finding_id: int
    scan_run_id: int
    source_revision_id: int
    candidate_id: int | None
    file_path: str
    start_line: int | None
    end_line: int | None
    symbol: str | None
    api_asset_id: int | None
    raw_severity: str
    final_severity: str | None
    ai_verdict: str | None
    ai_confidence: float | None
    risk_score: int | None
    status: str
    created_at: datetime


class FindingListOut(BaseModel):
    """漏洞列表精简版。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: str
    status: str
    api_asset_id: int | None
    file_path: str | None = None
    rule_id: int | None = None
    first_seen_commit: str | None = None
    last_seen_commit: str | None = None
    rule_key: str | None = None
    cwe: str | None = None
    ai_verdict: str | None = None
    api_path: str | None = None
    repository_id: int | None = None
    created_at: datetime


class EvidenceOut(BaseModel):
    """证据包输出。聚合 SARIF 片段、源码上下文、AI Review 响应等。"""

    finding_id: int
    sarif_fragment: dict[str, Any] | None = Field(default=None, description="SARIF result 片段")
    source_context: str | None = Field(default=None, description="源码上下文片段")
    ai_review_response: dict[str, Any] | None = Field(default=None, description="AI Review 响应")
    need_requests: list[dict[str, Any]] | None = Field(default=None, description="AI 请求补充信息")


class DataflowOut(BaseModel):
    """数据流可视化输出：Source → CallPath → Sink。"""

    source: dict[str, Any] = Field(..., description="源点位置 {file, line, symbol}")
    sink: dict[str, Any] = Field(..., description="汇点位置 {file, line, symbol}")
    dataflow_path: list[dict[str, Any]] = Field(
        default_factory=list, description="路径节点列表"
    )


class FindingStatusUpdate(BaseModel):
    """漏洞状态变更入参。"""

    status: str = Field(..., description="目标状态：OPEN/FIXED/REAPPEARED/FALSE_POSITIVE")
