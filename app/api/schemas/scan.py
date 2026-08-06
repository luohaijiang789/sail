"""扫描相关 DTO。

对应 ``app.domain.scan_run.ScanRun`` / ``ScanStageRun``。
涵盖扫描创建、状态查询、阶段时间线、流式日志、SSE 事件等场景的传输结构。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RevisionRef(BaseModel):
    """被扫描的代码版本引用。``type`` 为 branch/tag/commit。"""

    type: str = Field(..., description="引用类型：branch / tag / commit")
    value: str = Field(..., description="分支名 / tag 名 / commit SHA")


class ScanCreate(BaseModel):
    """创建扫描入参。"""

    repository_id: int = Field(..., description="仓库 ID")
    revision: RevisionRef = Field(..., description="被扫描的版本引用")
    scan_profile_id: int | None = Field(default=None, description="扫描配置 ID")
    ai_analysis: bool = Field(default=True, description="是否启用 AI 分析阶段")


class ScanOut(BaseModel):
    """扫描状态输出。对应 ``ScanRun`` 的运行态字段。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    current_stage: str | None
    progress: int
    build_quality: str | None
    started_at: datetime | None
    finished_at: datetime | None
    mode: str


class StageOut(BaseModel):
    """阶段运行输出。对应 ``ScanStageRun``。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    stage_type: str
    status: str
    attempt: int
    required: bool
    on_failure: str
    started_at: datetime | None
    finished_at: datetime | None
    error_code: str | None
    error_message: str | None


class ScanLogOut(BaseModel):
    """扫描日志分块输出。用于流式日志接口的非流式回退或调试。"""

    scan_run_id: int
    lines: list[str] = Field(default_factory=list, description="本次返回的日志行")
    has_more: bool = Field(default=False, description="是否还有后续日志")


class ScanEventOut(BaseModel):
    """SSE 事件输出。推送 ScanRun/ScanStageRun 状态变化。"""

    event: str = Field(..., description="事件类型，如 scan.status_changed / stage.status_changed")
    event_seq: int = Field(..., description="事件序号，用于 Last-Event-ID 断线重连")
    scan_id: int
    stage: str | None = Field(default=None, description="阶段类型，阶段事件时填充")
    status: str
    progress: int | None = Field(default=None)
    message: str | None = Field(default=None)
    data: dict[str, Any] | None = Field(default=None, description="附加数据")
