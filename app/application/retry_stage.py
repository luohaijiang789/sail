"""阶段重试应用服务。

对处于 FAILED_RETRYABLE / FAILED_FINAL / TIMEOUT 的 ScanStageRun 发起重试：
重置状态为 PENDING，attempt +1，重新派发 Celery 任务。
"""

from app.domain.scan_run import ScanRun  # noqa: F401  保留导入便于后续实现引用


def retry_stage(scan_run_id: int, stage_run_id: int) -> None:
    """重试指定阶段。

    Args:
        scan_run_id: 所属 ScanRun ID（用于校验与状态重算）。
        stage_run_id: 待重试的 ScanStageRun ID。
    """
    raise NotImplementedError
