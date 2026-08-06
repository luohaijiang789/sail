"""Worker → API 回调客户端。

Worker 完成后通过 HTTP 回调通知编排器，不依赖 Celery 结果通道。
"""

from typing import Any

from app.config import settings
from app.core.logging import get_logger


class StageCallbackClient:
    """阶段回调客户端。Worker 用它通知 API 阶段完成/失败。"""

    def __init__(self, api_base_url: str | None = None) -> None:
        self.api_base_url = api_base_url or f"http://{settings.api_host}:{settings.api_port}"
        self.logger = get_logger("StageCallbackClient")

    async def notify_complete(self, stage_run_id: int, result: dict[str, Any]) -> None:
        """通知阶段完成。"""
        # TODO: POST /internal/stages/{stage_run_id}/complete
        raise NotImplementedError

    async def notify_fail(self, stage_run_id: int, error_code: str,
                          error_message: str, retryable: bool) -> None:
        """通知阶段失败。"""
        # TODO: POST /internal/stages/{stage_run_id}/fail
        raise NotImplementedError

    async def update_heartbeat(self, stage_run_id: int) -> None:
        """更新心跳。"""
        # TODO: POST /internal/stages/{stage_run_id}/heartbeat
        raise NotImplementedError


# 单例
callback_client = StageCallbackClient()
