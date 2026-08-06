"""Worker 基类：所有阶段 Worker 的公共逻辑。

13 个 Worker 继承 BaseStageWorker，只需实现 _execute() 方法。
公共逻辑：DB session 管理、日志上下文绑定、幂等检查、心跳更新、回调通知。
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.core.logging import bind_scan_context, get_logger, unbind_context
from app.core.result import StageResult


class BaseStageWorker(ABC):
    """阶段 Worker 基类。"""

    stage_type: str = ""

    def __init__(self, scan_run_id: int, stage_run_id: int) -> None:
        self.scan_run_id = scan_run_id
        self.stage_run_id = stage_run_id
        self.logger = get_logger(self.__class__.__name__)

    def run(self) -> StageResult:
        """执行入口。公共逻辑 + 子类 _execute()。"""
        self._bind_context()
        self.logger.info("stage_started", stage_type=self.stage_type)

        try:
            # 幂等检查：已成功的阶段直接跳过
            if self._check_idempotent():
                self.logger.info("stage_skipped_idempotent")
                return StageResult.skipped("idempotent match")

            # 更新阶段状态为 RUNNING
            self._update_status("RUNNING")

            # 执行子类逻辑
            result = self._execute()

            # 回调通知
            self._notify_complete(result)

            self.logger.info("stage_finished", status=result.status)
            return result

        except Exception as e:
            self.logger.exception("stage_failed", error=str(e))
            result = self._handle_exception(e)
            self._notify_fail(result)
            return result

        finally:
            unbind_context()

    @abstractmethod
    def _execute(self) -> StageResult:
        """子类实现：实际执行逻辑。"""
        ...

    # === 公共方法 ===

    def _bind_context(self) -> None:
        """绑定日志上下文。"""
        bind_scan_context(scan_run_id=self.scan_run_id, stage_run_id=self.stage_run_id)

    def _check_idempotent(self) -> bool:
        """幂等检查：已成功的阶段且 input_fingerprint 匹配则跳过。"""
        # TODO: 查 scan_stage_run 表
        return False

    def _update_status(self, status: str, **extra: Any) -> None:
        """更新阶段状态 + 心跳。"""
        # TODO: UPDATE scan_stage_run SET status=?, heartbeat_at=NOW()
        ...

    def _update_heartbeat(self) -> None:
        """更新心跳时间。"""
        # TODO: UPDATE scan_stage_run SET heartbeat_at=NOW()
        ...

    def _notify_complete(self, result: StageResult) -> None:
        """通知编排器阶段完成。"""
        # TODO: POST /internal/stages/{stage_run_id}/complete
        ...

    def _notify_fail(self, result: StageResult) -> None:
        """通知编排器阶段失败。"""
        # TODO: POST /internal/stages/{stage_run_id}/fail
        ...

    def _handle_exception(self, exc: Exception) -> StageResult:
        """异常转 StageResult。"""
        from app.core.exceptions import SailError, classify_error

        if isinstance(exc, SailError):
            category = classify_error(exc.error_code)
            retryable = category in ("RETRYABLE", "RESOURCE")
            return StageResult.failure(exc.error_code, exc.message, retryable=retryable)

        return StageResult.failure("UNKNOWN_ERROR", str(exc), retryable=False)
