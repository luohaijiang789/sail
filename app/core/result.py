"""结果包装器：统一 API 和 Worker 的返回结构。"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应。"""
    success: bool = True
    data: T | None = None
    error: dict[str, Any] | None = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error_code: str, message: str, **context: Any) -> "ApiResponse[T]":
        return cls(success=False, error={"code": error_code, "message": message, "context": context})


class StageResult(BaseModel):
    """Worker 阶段执行结果。"""
    status: str  # SUCCEEDED / FAILED_RETRYABLE / FAILED_FINAL / SKIPPED
    output_artifact_id: int | None = None
    output_data: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    retryable: bool = False
    metrics: dict[str, Any] | None = None

    @classmethod
    def success(cls, artifact_id: int | None = None, **data: Any) -> "StageResult":
        return cls(status="SUCCEEDED", output_artifact_id=artifact_id, output_data=data)

    @classmethod
    def failure(cls, error_code: str, message: str, retryable: bool = False) -> "StageResult":
        return cls(status="FAILED_RETRYABLE" if retryable else "FAILED_FINAL",
                   error_code=error_code, error_message=message, retryable=retryable)

    @classmethod
    def skipped(cls, reason: str = "") -> "StageResult":
        return cls(status="SKIPPED", output_data={"reason": reason})


class PaginatedResult(BaseModel, Generic[T]):
    """分页结果。"""
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool = False
