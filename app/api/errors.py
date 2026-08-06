"""FastAPI 全局异常处理器。

把三类异常统一收敛为 ``ApiResponse.fail()`` 结构，保证前端只面对一种错误体：
- ``SailError`` → 按 ``error.http_status`` 返回（默认 500）
- ``RequestValidationError`` → 422，字段级错误明细
- 通用 ``Exception`` → 500，掩盖内部错误避免泄露栈

注册入口 ``register_exception_handlers(app)`` 在 ``main.py`` 启动时调用一次。
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.exceptions import SailError
from app.core.logging import get_logger
from app.core.result import ApiResponse

_logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """向 ``app`` 注册 SailError / 校验错误 / 通用异常处理器。"""

    @app.exception_handler(SailError)
    async def handle_sail_error(_request: Request, exc: SailError) -> JSONResponse:
        """业务异常：按 ``http_status`` 返回 ``ApiResponse.fail()``。"""
        response = ApiResponse.fail(
            error_code=exc.error_code,
            message=exc.message,
            retryable=exc.retryable,
            **exc.context,
        )
        return JSONResponse(status_code=exc.http_status, content=response.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """请求体/参数校验失败：422，附 pydantic 错误明细。"""
        response = ApiResponse.fail(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            errors=exc.errors(),
        )
        return JSONResponse(status_code=422, content=response.model_dump())

    @app.exception_handler(ValidationError)
    async def handle_validation_error(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        """模型层 pydantic 校验失败：422，附错误明细。"""
        response = ApiResponse.fail(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            errors=exc.errors(),
        )
        return JSONResponse(status_code=422, content=response.model_dump())

    @app.exception_handler(Exception)
    async def handle_unhandled_error(_request: Request, exc: Exception) -> JSONResponse:
        """兜底：未知异常一律 500，对外不暴露堆栈，仅记日志。"""
        _logger.exception("unhandled_exception", error=str(exc))
        response: ApiResponse[Any] = ApiResponse.fail(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
        )
        return JSONResponse(status_code=500, content=response.model_dump())
